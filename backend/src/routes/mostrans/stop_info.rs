use crate::types::Environment;
use crate::types::mostrans::stop::StopInfoResponse;
use actix_web::{HttpResponse, error, get, web};

#[get("/stop_info/{id}")]
pub async fn get_stop_info(
    id: web::Path<String>,
    env: web::Data<Environment>,
    client: web::Data<awc::Client>,
) -> error::Result<HttpResponse> {
    let mut stop_info_response = client
        .get(format!("{}/stop_v2/{id}", env.moscowapp_api_url))
        .insert_header((
            "User-Agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
        ))
        .send()
        .await
        .map_err(|_| error::ErrorGatewayTimeout("Error sending API request"))?;

    if !stop_info_response.status().is_success() {
        return Err(error::ErrorNotFound("Stop not found"));
    };

    let mut stop_info = stop_info_response.json::<StopInfoResponse>().await.unwrap();

    stop_info.route_path = stop_info
        .route_path
        .into_iter()
        .filter(|rp| rp.route_type == "tram")
        .collect();

    Ok(HttpResponse::Ok().json(stop_info))
}
