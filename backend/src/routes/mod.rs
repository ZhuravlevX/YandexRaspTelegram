mod mosmetro;
mod mostrans;

use actix_web::web;

pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.configure(mosmetro::configure)
        .configure(mostrans::configure);
}
