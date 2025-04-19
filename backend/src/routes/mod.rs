mod getters;
mod route;
mod search;
mod wagons;

use crate::routes::getters::{
    get_line, get_notifications, get_schema, get_station, get_station_mini,
};
use crate::routes::route::get_route;
use crate::routes::search::get_search;
use crate::routes::wagons::get_wagons;
use actix_web::web;

pub fn configure_routes(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/station")
            .service(get_search)
            .service(get_station_mini)
            .service(get_station),
    );
    cfg.service(get_schema);
    cfg.service(get_notifications);
    cfg.service(get_line);
    cfg.service(get_route);
    cfg.service(get_wagons);
}
