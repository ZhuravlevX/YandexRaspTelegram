use crate::state::AppState;
use actix_web::{error, get, web, HttpResponse, Responder};

#[get("/wagons/{station_id}")]
pub async fn get_wagons(
    client: web::Data<awc::Client>,
    state: web::Data<AppState>,
    station_id: web::Path<usize>,
) -> error::Result<impl Responder> {
    let res = client
        .get(format!(
            "{}/stations/v2/{}/wagons",
            &state.env.mosmetro_api_url, station_id
        ))
        .insert_header((
            "User-Agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
        ))
        .send()
        .await
        .map_err(error::ErrorGatewayTimeout)?;

    Ok(HttpResponse::build(res.status())
        .insert_header(("Content-Type", "application/json"))
        .streaming(res))
}
