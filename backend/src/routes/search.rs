use crate::functions::convert_in_station_mini;
use crate::types::schema::Station;
use crate::types::{AppState, StationMini};
use actix_web::{get, web, HttpResponse, Responder};
use serde::{Deserialize, Serialize};
use strsim::jaro_winkler;

#[derive(Deserialize)]
struct Query {
    q: String,
    limit: Option<usize>,
}

#[derive(Debug)]
struct SearchResult<'a> {
    station: &'a Station,
    score: f64,
}

#[derive(Serialize)]
struct Response {
    success: bool,
    count: usize,
    stations: Vec<StationMini>,
}

#[get("/search")]
async fn get_search(query: web::Query<Query>, state: web::Data<AppState>) -> impl Responder {
    let schema_read = state.schema.read();
    let Some(schema) = schema_read.as_ref() else {
        return HttpResponse::ServiceUnavailable().finish();
    };

    if query.q.chars().count() < 3 {
        return HttpResponse::BadRequest().body("Search query too short. 3 symbols min");
    }

    let mut result: Vec<SearchResult> = schema
        .stations
        .iter()
        .filter_map(|station| {
            let station_name: String = station
                .name
                .ru
                .clone()
                .to_lowercase()
                .chars()
                .take(query.q.chars().count() + 1)
                .collect();
            
            match jaro_winkler(query.q.to_lowercase().as_str(), station_name.as_str()) {
                ..0.85 => None,
                score @ _ => Some(SearchResult { station, score }),
            }
        })
        .collect();
    
    if result.is_empty() {
        return HttpResponse::NotFound().finish();
    }

    let limit = query.limit.unwrap_or(10).min(100);

    result.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
    let stations: Vec<StationMini> = result
        .into_iter()
        .map(|s| convert_in_station_mini(s.station, schema))
        .take(limit)
        .collect();

    let response = Response {
        success: true,
        count: stations.len(),
        stations,
    };

    HttpResponse::Ok().json(response)
}
