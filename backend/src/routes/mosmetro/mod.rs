use crate::routes::mosmetro::route::get_route;
use crate::routes::mosmetro::station::{get_station, get_station_mini};
use crate::routes::mosmetro::troika::card_number::get_troika_by_card_number;
use crate::routes::mosmetro::troika::my_transport_card::connect_otp::get_connect_otp;
use crate::routes::mosmetro::troika::my_transport_card::get_my_transport_card;
use crate::routes::mosmetro::wagons::get_wagons;
use crate::state::AppState;
use crate::utils::mosmetro::search::find_line_by_id;
use actix_web::{get, web, HttpResponse, Responder};
use station::search::get_search;

pub mod route;
mod station;
mod troika;
pub mod wagons;

pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::scope("/mosmetro")
            .service(
                web::scope("/station")
                    .service(get_search)
                    .service(get_station_mini)
                    .service(get_station),
            )
            .service(
                web::scope("/troika")
                    .service(get_troika_by_card_number)
                    .service(
                        web::scope("/my_transport_card")
                            .service(get_my_transport_card)
                            .service(get_connect_otp),
                    ),
            )
            .service(get_schema)
            .service(get_notifications)
            .service(get_line)
            .service(get_route)
            .service(get_wagons),
    );
}

#[get("/schema")]
pub async fn get_schema(state: web::Data<AppState>) -> impl Responder {
    if let Some(schema) = state.schema.read().as_ref() {
        HttpResponse::Ok().json(schema)
    } else {
        HttpResponse::ServiceUnavailable().body("Schema not loaded yet")
    }
}

#[get("/notifications")]
pub async fn get_notifications(state: web::Data<AppState>) -> impl Responder {
    if let Some(notifications) = state.notifications.read().as_ref() {
        HttpResponse::Ok().json(notifications)
    } else {
        HttpResponse::ServiceUnavailable().body("Notifications not loaded yet")
    }
}

#[get("/line/{line_id}")]
pub async fn get_line(id: web::Path<usize>, state: web::Data<AppState>) -> impl Responder {
    let schema_read = state.schema.read();
    let Some(schema) = schema_read.as_ref() else {
        return HttpResponse::ServiceUnavailable().body("Schema not loaded yet");
    };

    match find_line_by_id(id.into_inner(), schema) {
        Some(line) => HttpResponse::Ok().json(line),
        None => HttpResponse::NotFound().finish(),
    }
}
