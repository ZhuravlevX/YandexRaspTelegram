use crate::state::AppState;
use crate::types::mostrans::route::RouteDataResponse;
use crate::types::mostrans::suggest::SuggestResponse;
use actix_web::{error, get, web, HttpResponse};
use url::Url;

#[get("/suggest/{query}")]
pub async fn get_suggest(
    query: web::Path<String>,
    state: web::Data<AppState>,
    client: web::Data<awc::Client>,
) -> error::Result<HttpResponse> {
    let key = &query.to_string();

    let route_data = match state.suggest_cache.get(key).await {
        Some(cached) => cached,
        None => {
            let mut res = client
                .get(Url::parse(&format!("https://api.moscowapp.mos.ru/v8.2/suggest?query={key}&types=Route")).unwrap().to_string())
                .insert_header((
                    "User-Agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
                ))
                .send()
                .await
                .map_err(|_|
                    error::ErrorGatewayTimeout("Error sending API request")
                )?;

            if !res.status().is_success() {
                return Err(error::ErrorNotFound("Route not found"));
            };

            let mut suggest_response = res.json::<SuggestResponse>().await.unwrap();

            suggest_response.data = suggest_response
                .data
                .into_iter()
                .filter(|item| item.name.eq("Трамвай"))
                .collect();

            if suggest_response.data.is_empty() {
                return Err(error::ErrorNotFound("No suggest"));
            }

            let route_id = suggest_response.data[0].id.clone();

            let mut res = client.get(format!("https://api.moscowapp.mos.ru/v8.2/route_v3/{route_id}")).insert_header((
                "User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
            ))
                .send()
                .await
                .map_err(|_|
                    error::ErrorGatewayTimeout("Error sending API request")
                )?;

            if !res.status().is_success() {
                return Err(error::ErrorNotFound("Route info not found"));
            };

            let route_data = res.json::<RouteDataResponse>().await.unwrap();

            state
                .suggest_cache
                .insert(key.clone(), route_data.clone())
                .await;

            route_data

            // let data = suggest_response.data[0].clone();
            //
            // let suggest_data = SuggestData {
            //     id: data.id,
            //     description: data.description,
            //     name: data.name,
            //     route_number: data.route.number,
            // };
            //
            // state
            //     .suggest_cache
            //     .insert(key.clone(), suggest_data.clone())
            //     .await;
            //
            // suggest_data
        }
    };

    Ok(HttpResponse::Ok().json(route_data))
}
