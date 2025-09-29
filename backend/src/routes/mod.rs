mod mosmetro;
mod mostrans;
mod status;

use actix_web::web;

pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.configure(mosmetro::configure)
        .configure(mostrans::configure);
}
