use crate::types::Environment;
use crate::types::mostrans::stop::StopInfoResponse;
use actix_web::{HttpResponse, error, get, web};

#[get("/stop_info/{id}")]
pub async fn get_stop_info(
    id: web::Path<String>,
    env: web::Data<Environment>,
    client: web::Data<reqwest::Client>,
) -> error::Result<HttpResponse> {
    let stop_info_response = client
        .get(format!("{}/stop_v2/{id}", env.moscowapp_api_url))
        .send()
        .await
        .map_err(error::ErrorBadGateway)?;

    if !stop_info_response.status().is_success() {
        return Err(error::ErrorNotFound("Stop not found"));
    };

    let mut stop_info = stop_info_response
        .json::<StopInfoResponse>()
        .await
        .map_err(error::ErrorInternalServerError)?;

    stop_info.route_path = stop_info
        .route_path
        .into_iter()
        .filter(|rp| rp.route_type == "tram")
        .collect();

    Ok(HttpResponse::Ok().json(stop_info))
}
