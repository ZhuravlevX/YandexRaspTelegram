use crate::functions::convert_in_station_mini;
use crate::functions::getters::find_station_by_id;
use crate::functions::route_time::calc_route_time;
use crate::types::router::{RouterRequest, RouterResponse};
use crate::types::StationMini;
use crate::AppState;
use actix_web::{get, web, HttpResponse, Responder};
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
) -> impl Responder {
    let mut router_res = client
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
        .unwrap();

    if !router_res.status().is_success() {
        return HttpResponse::BadRequest().finish();
    }

    let schema_read = state.schema.read();
    let Some(schema) = schema_read.as_ref() else {
        return HttpResponse::ServiceUnavailable().body("Schema not loaded yet");
    };

    let router_res = router_res.json::<RouterResponse>().await.unwrap();

    let nodes: Vec<StationMini> = router_res.data[0]
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
        duration: router_res.data[0].time,
    };

    for i in parts.into_iter() {
        res.parts.push(Part {
            nodes: i.clone(),
            duration: calc_route_time(i.iter().map(|s| s.id).collect(), schema),
        })
    }

    HttpResponse::Ok().json(res)
}
