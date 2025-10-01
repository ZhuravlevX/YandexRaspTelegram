use crate::routes::configure_routes;
use crate::types::Environment;
use actix_cors::Cors;
use actix_web::{App, HttpServer, middleware::Logger, rt, web};
use env_logger::Env;
use jiff::Zoned;
use jiff::civil::DateTime;
use log::info;
use state::AppState;
use std::io::Write;
use std::sync::Arc;
use utils::scheduled_tasks::updater::updater;

mod routes;
mod state;
mod types;
mod utils;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // init logger
    env_logger::Builder::from_env(Env::default().default_filter_or("info"))
        .format(|buf, record| {
            let timestamp = DateTime::from(Zoned::now());
            let style = buf.default_level_style(record.level());
            writeln!(
                buf,
                "[{:.0} {style}{}{style:#} {}] {}",
                timestamp,
                record.level(),
                record.module_path().unwrap_or_default(),
                record.args()
            )
        })
        .init();

    info!("Starting API Server");

    // init env
    dotenvy::dotenv().ok();
    let env = envy::from_env::<Environment>().expect("Failed to read environment variables");
    info!("Environment variables successfully loaded!");

    // init app state
    let app_state = Arc::new(AppState::new(env.clone()));
    rt::spawn(updater(app_state.clone(), env.mosmetro_api_url.clone())); // spawn data updater thread

    // get host and port
    let host = env.host.clone();
    let port = env.port.clone();

    HttpServer::new(move || {
        App::new()
            .wrap(Logger::default())
            .wrap(Cors::permissive())
            .configure(configure_routes)
            .app_data(web::Data::from(app_state.clone()))
            .app_data(web::Data::new(awc::Client::new()))
            .app_data(web::Data::new(env.clone()))
    })
    .bind((host, port))?
    .workers(4)
    .run()
    .await
}
