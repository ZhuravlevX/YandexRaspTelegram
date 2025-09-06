use crate::routes::configure_routes;
use crate::types::Environment;
use actix_cors::Cors;
use actix_web::{middleware::Logger, rt, web, App, HttpServer};
use env_logger::Env;
use log::info;
use state::AppState;
use std::sync::Arc;
use utils::scheduled_tasks::cache_cleaner::cache_cleaner;
use utils::scheduled_tasks::updater::updater;

mod routes;
mod state;
mod types;
mod utils;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // init logger
    env_logger::init_from_env(Env::default().default_filter_or("info"));
    info!("Starting API Server");

    // init env
    dotenvy::dotenv().ok();
    let env = envy::from_env::<Environment>().expect("Failed to read environment variables");
    info!("Env loaded");

    // init app state
    let app_state = Arc::new(AppState::new(env.clone()));
    rt::spawn(updater(app_state.clone(), env.mosmetro_api_url.clone())); // spawn data updater thread
    rt::spawn(cache_cleaner(app_state.clone()));

    HttpServer::new(move || {
        App::new()
            .wrap(Logger::default())
            .wrap(Cors::permissive())
            .configure(configure_routes)
            .app_data(web::Data::from(app_state.clone()))
            .app_data(web::Data::new(awc::Client::new()))
    })
    .bind((env.host, env.port))?
    .workers(4)
    .run()
    .await
}
