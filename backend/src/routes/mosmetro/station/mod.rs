use crate::state::AppState;
use crate::utils::mosmetro::schema::convert_in_station_mini;
use crate::utils::mosmetro::search::find_station_by_id;
use actix_web::{get, web, HttpResponse, Responder};

pub mod search;

// /station/{id}
#[get("/{station_id}")]
pub async fn get_station(id: web::Path<usize>, state: web::Data<AppState>) -> impl Responder {
    let schema_read = state.schema.read();
    let Some(schema) = schema_read.as_ref() else {
        return HttpResponse::ServiceUnavailable().body("Schema not loaded yet");
    };

    match find_station_by_id(id.into_inner(), schema) {
        Some(station) => HttpResponse::Ok().json(station),
        None => HttpResponse::NotFound().finish(),
    }
}

// /station/mini/{id}
// minimal info about station
#[get("/mini/{station_id}")]
pub async fn get_station_mini(id: web::Path<usize>, state: web::Data<AppState>) -> impl Responder {
    let schema_read = state.schema.read();
    let Some(schema) = schema_read.as_ref() else {
        return HttpResponse::ServiceUnavailable().body("Schema not loaded yet");
    };

    match find_station_by_id(id.into_inner(), schema).map(|s| convert_in_station_mini(s, schema)) {
        Some(station) => HttpResponse::Ok().json(station),
        None => HttpResponse::NotFound().finish(),
    }
}
