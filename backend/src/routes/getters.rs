use crate::functions::convert_in_station_mini;
use crate::functions::getters::{find_line_by_id, find_station_by_id};
use crate::types::AppState;
use actix_web::{get, web, HttpResponse, Responder};

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
