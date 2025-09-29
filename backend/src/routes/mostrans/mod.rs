use crate::routes::mostrans::stop_info::get_stop_info;
use crate::routes::mostrans::suggest::get_suggest;
use crate::routes::mostrans::troika::card_number::get_troika_by_card_number;
use crate::routes::mostrans::troika::products::get_troika_products;
use actix_web::web;

mod stop_info;
mod suggest;
mod troika;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/mostrans")
            .service(get_suggest)
            .service(get_stop_info)
            .service(get_troika_by_card_number)
            .service(get_troika_products),
    );
}
