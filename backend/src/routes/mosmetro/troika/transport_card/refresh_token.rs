// use actix_web::{HttpResponse, error, get, web};
// use reqwest::header::AUTHORIZATION;
// use serde::Deserialize;
// use serde_json::json;

// use crate::types::Environment;

// #[get("/refresh_token/{refresh_token}")]
// pub async fn get_connect_otp(
//     env: web::Data<Environment>,
//     client: web::Data<reqwest::Client>,
// ) -> error::Result<HttpResponse> {
//     let res = client.post(format!("{}/connect/token", env.mosmetro_auth_url))
//         .header(AUTHORIZATION, "Basic ZjljM2M4NTktOTc3YS00ZWI3LTliY2UtNDM2OTk2NGRmODU1OlJkb3pEZjkzakxLcDI2MzVFcG1KVUwzbWM2bzFVSw==").body(json!(
//         {
//             "grant_type": "otp",
//             "key": query.otp,
//             "password": query.password
//         }
//         ).to_string()).send().await.map_err(error::ErrorBadGateway);

//     Ok(())
// }
