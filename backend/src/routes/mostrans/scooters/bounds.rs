use crate::types::mostrans::scooters::{BoundsResponse, Scooter};
use crate::types::Environment;
use actix_web::{error, get, web, HttpResponse};
use serde::{Deserialize, Serialize};
use std::fmt::Display;

#[derive(Deserialize)]
struct Query {
    lat1: String,
    lon1: String,
    lat2: String,
    lon2: String,
}

#[derive(Serialize)]
struct Response {
    scooters: Vec<Scooter>,
}

impl Response {
    fn from_scooters_vec(scooters: Vec<Scooter>) -> Self {
        Self { scooters }
    }
}

#[get("/bounds")]
pub async fn get_scooter_bounds(
    client: web::Data<reqwest::Client>,
    query: web::Query<Query>,
    env: web::Data<Environment>,
) -> error::Result<HttpResponse> {
    let bounds = format!(
        "{}%2C{}%3B{}%2C{}",
        query.lat1, query.lon1, query.lat2, query.lon2
    );
    let bounds_response = client
        .get(format!(
            "https://api.moscowapp.mos.ru/v8.2/scooter/universal?bounds={bounds}"
        ))
        .header("XAuthToken", &env.xauth_token_moscowapp)
        .send()
        .await
        .map_err(error::ErrorBadGateway)?;

    let scooters = bounds_response
        .json::<BoundsResponse>()
        .await
        .map_err(|e| error::ErrorInternalServerError(format!("{:?}", e)))?;

    let scooters_fetches = scooters
        .into_iter()
        .map(|scooter| fetch_scooter(scooter.id, client.clone(), env.clone()))
        .collect::<Vec<_>>();

    let scooters_responses = futures::future::join_all(scooters_fetches).await;

    let mut scooters_data = Vec::with_capacity(scooters_responses.len());
    for scooter in scooters_responses {
        scooters_data.push(scooter?);
    }

    Ok(HttpResponse::Ok().json(Response::from_scooters_vec(scooters_data)))
}

async fn fetch_scooter(
    scooter_id: impl Display,
    client: web::Data<reqwest::Client>,
    env: web::Data<Environment>,
) -> error::Result<Scooter> {
    let scooter_response = client
        .get(format!(
            "https://api.moscowapp.mos.ru/v8.2/scooter/universal/{scooter_id}"
        ))
        .header("XAuthToken", &env.xauth_token_moscowapp)
        .send()
        .await
        .map_err(error::ErrorBadGateway)?;

    scooter_response
        .json::<Scooter>()
        .await
        .map_err(|e| error::ErrorInternalServerError(format!("{:?}", e)))
}
