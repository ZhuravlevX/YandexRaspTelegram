use actix_web::{HttpResponse, error, get, web};
use reqwest::header::AUTHORIZATION;
use serde_json::json;

use crate::types::Environment;

#[get("/connect_otp/{phone_number}")]
pub async fn get_connect_otp(
    phone_number: web::Path<String>,
    env: web::Data<Environment>,
    client: web::Data<reqwest::Client>,
) -> error::Result<HttpResponse> {
    let res = client
        .post(format!("{}/connect/otp", env.mosmetro_auth_url))
        // .basic_auth("Basic", Some("ZjljM2M4NTktOTc3YS00ZWI3LTliY2UtNDM2OTk2NGRmODU1OlJkb3pEZjkzakxLcDI2MzVFcG1KVUwzbWM2bzFVSw=="))
        .header(AUTHORIZATION, "Basic ZjljM2M4NTktOTc3YS00ZWI3LTliY2UtNDM2OTk2NGRmODU1OlJkb3pEZjkzakxLcDI2MzVFcG1KVUwzbWM2bzFVSw==")
        .body(json!(
        {
            "username": *phone_number,
            "scope": "openid offline_access nbs.ppa idps phone email all"
        }
        ).to_string())
        .send()
        .await
        .map_err(error::ErrorBadGateway)?;

    Ok(HttpResponse::Ok().body(res.text().await.unwrap()))
}
