use crate::routes::mostrans::stop_info::get_stop_info;
use crate::routes::mostrans::suggest::get_suggest;
use actix_web::web;

mod stop_info;
mod suggest;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/mostrans")
            .service(get_suggest)
            .service(get_stop_info),
    );
}
