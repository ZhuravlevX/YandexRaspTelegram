use crate::state::AppState;
use crate::types::mosmetro::router::{RouterRequest, RouterResponse};
use crate::types::mosmetro::StationMini;
use crate::utils::mosmetro::schema::calculate_route_time;
use crate::utils::mosmetro::schema::convert_in_station_mini;
use crate::utils::mosmetro::search::find_station_by_id;
use actix_web::{error, get, web, HttpResponse, Responder};
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct Query {
    from: usize,
    to: usize,
}

#[derive(Serialize)]
struct Response {
    success: bool,
    parts: Vec<Part>,
    duration: u32,
}

#[derive(Serialize)]
struct Part {
    nodes: Vec<StationMini>,
    duration: u32,
}

#[get("/route")]
pub async fn get_route(
    query: web::Query<Query>,
    client: web::Data<awc::Client>,
    state: web::Data<AppState>,
) -> error::Result<impl Responder> {
    let key = format!("{}-{}", query.from, query.to);

    // let cached_res = {
    //     let cache = state.route_cache.read();
    //     cache.get(&key).cloned()
    // };

    let cached_response = state.route_cache.get(&key).await;

    let router_response = match cached_response {
        Some(route_cache) => route_cache,
        None => {
            let mut res = client
                .post(&state.env.router_api_url)
                .insert_header((
                    "User-Agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
                ))
                .send_json(&RouterRequest {
                    from: query.from,
                    to: query.to,
                })
                .await
                .map_err(|_| error::ErrorGatewayTimeout("Error sending route request"))?;

            if !res.status().is_success() {
                return Err(error::ErrorNotFound("Route not found"));
            }

            let router_res = res.json::<RouterResponse>().await.unwrap();
            state.route_cache.insert(key, router_res.clone()).await;
            router_res
        }
    };

    let schema_read = state.schema.read();
    let schema = schema_read
        .as_ref()
        .ok_or(error::ErrorServiceUnavailable("Schema not loaded yet"))?;

    let nodes: Vec<StationMini> = router_response.data[0]
        .nodes
        .iter()
        .filter_map(|id| {
            find_station_by_id(*id, schema).map(|s| convert_in_station_mini(s, schema))
        })
        .collect();

    // делим на куски с пересадками
    let mut parts: Vec<Vec<StationMini>> = vec![vec![nodes[0].clone()]];

    let mut curr: usize = 0;
    for i in 1..nodes.len() {
        if nodes[i].line_id != nodes[i - 1].line_id {
            curr += 1;
            parts.push(Vec::new())
        }
        parts[curr].push(nodes[i].clone());
    }

    // собираем ответ
    let mut res = Response {
        success: true,
        parts: Vec::new(),
        duration: router_response.data[0].time,
    };

    for i in parts.into_iter() {
        res.parts.push(Part {
            nodes: i.clone(),
            duration: calculate_route_time(i.iter().map(|s| s.id).collect(), schema),
        })
    }

    Ok(HttpResponse::Ok().json(res))
}
