use crate::types::Environment;
use crate::types::mostrans::troika::{CardInfoResponse, CardSearchResponse};
use actix_web::{HttpResponse, error, get, web};

#[get("/troika/card_number/{card_number}")]
pub async fn get_troika_by_card_number(
    env: web::Data<Environment>,
    client: web::Data<awc::Client>,
    card_number: web::Path<String>,
) -> error::Result<HttpResponse> {
    let mut search_response = client
        .get(format!(
            "{}/cards/v1.0?cardNumber={card_number}",
            env.lk_mosmetro_api_url
        ))
        .insert_header((
            "User-Agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
        ))
        .send()
        .await
        .map_err(error::ErrorBadGateway)?;

    let search_data = search_response
        .json::<CardSearchResponse>()
        .await
        .map_err(error::ErrorInternalServerError)?;

    let Some(card) = search_data.cards.first() else {
        return Err(error::ErrorNotFound("No card found by this ID"));
    };

    let card_uid = card.uid.clone();

    let mut card_info_response = client
        .get(format!(
            "https://lk.mosmetro.ru/api/cards/v1.0/{card_uid}/validate/payment"
        ))
        .insert_header((
            "User-Agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
        ))
        .send()
        .await
        .map_err(error::ErrorBadGateway)?;

    let card_info_response_data = card_info_response
        .json::<CardInfoResponse>()
        .await
        .map_err(error::ErrorInternalServerError)?;

    if !card_info_response_data.success {
        return Err(error::ErrorInternalServerError("Card Info request failed"));
    }

    let mut card_info = card_info_response_data.data.card.clone();

    card_info.img = format!("https://lk.mosmetro.ru/api{}", card_info.img);

    Ok(HttpResponse::Ok().json(card_info))
}
