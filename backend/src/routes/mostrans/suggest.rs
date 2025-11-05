use crate::state::AppState;
use crate::types::mostrans::route::RouteDataResponse;
use crate::types::mostrans::suggest::SuggestResponse;
use crate::types::Environment;
use actix_web::{error, get, web, HttpResponse};
use serde::Deserialize;
use std::fmt::Display;

#[derive(Deserialize)]
struct Query {
    #[serde(rename = "type")]
    suggest_type: Option<String>,
}

#[get("/suggest/{key}")]
pub async fn get_suggest(
    key: web::Path<String>,
    query: web::Query<Query>,
    state: web::Data<AppState>,
    client: web::Data<reqwest::Client>,
    env: web::Data<Environment>,
) -> error::Result<HttpResponse> {
    let key = &key.to_string();

    let route_data = match state
        .suggest_cache
        .get(&(query.suggest_type.clone(), key.clone()))
        .await
    {
        Some(cached) => cached,
        None => {
            let route_data =
                fetch_route_data(key, &query.suggest_type, client.clone(), env.clone()).await?;
            state
                .suggest_cache
                .insert(
                    (query.suggest_type.clone(), key.clone()),
                    route_data.clone(),
                )
                .await;

            route_data
        }
    };

    Ok(HttpResponse::Ok().json(route_data))
}

async fn fetch_route_data(
    key: impl Display,
    suggest_type: &Option<String>,
    client: web::Data<reqwest::Client>,
    env: web::Data<Environment>,
) -> error::Result<RouteDataResponse> {
    let suggest_response = client
        .get(format!(
            "{}/suggest?query={key}&types=Route",
            env.moscowapp_api_url
        ))
        .send()
        .await
        .map_err(error::ErrorBadGateway)?;

    if !suggest_response.status().is_success() {
        return Err(error::ErrorNotFound("Route not found"));
    };

    let mut suggest_data = suggest_response
        .json::<SuggestResponse>()
        .await
        .map_err(|e| error::ErrorInternalServerError(format!("{:?}", e)))?;

    match suggest_type {
        None => {}
        Some(suggest_type) => {
            suggest_data.data = suggest_data
                .data
                .into_iter()
                .filter(|item| item.name.eq(suggest_type))
                .collect();
        }
    }

    if suggest_data.data.is_empty() {
        return Err(error::ErrorNotFound("No suggest was found"));
    }

    let route_id = suggest_data.data[0].id.clone();

    let res = client
        .get(format!(
            "https://api.moscowapp.mos.ru/v8.2/route_v3/{route_id}"
        ))
        .send()
        .await
        .map_err(error::ErrorBadGateway)?;

    if !res.status().is_success() {
        return Err(error::ErrorNotFound("Route info not found"));
    };

    res.json::<RouteDataResponse>()
        .await
        .map_err(|e| error::ErrorInternalServerError(format!("{:?}", e)))
}
