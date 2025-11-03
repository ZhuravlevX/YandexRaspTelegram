pub mod connect_otp;
pub mod connect_token;
pub mod refresh_token;

use crate::types::mosmetro::troika::linked_cards::{DeferredAction, LinkedCardsResponse, Ticket};
use crate::types::mosmetro::troika::operations::{
    DeferredWrite, OperationsResponse, Payment, Transfer,
};
use crate::types::mosmetro::troika::trips::TripsResponse;
use crate::types::mosmetro::troika::{linked_cards, operations, trips};
use crate::types::Environment;
use actix_web::error::InternalError;
use actix_web::http::StatusCode;
use actix_web::{error, get, web, HttpResponse};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::time::SystemTime;

macro_rules! is_success_response {
    ($response:ident) => {
        if !$response.status().is_success() {
            let status_code = $response.status().as_u16();
            return Err(InternalError::new(
                $response.text().await.unwrap_or_default(),
                StatusCode::from_u16(status_code).unwrap_or(StatusCode::INTERNAL_SERVER_ERROR),
            )
            .into());
        }
    };
}

#[derive(Deserialize)]
struct QueryParams {
    access_token: String,
    // card_number: Option<String>,
}

#[get("/")]
pub async fn get_my_transport_card(
    query: web::Query<QueryParams>,
    env: web::Data<Environment>,
    client: web::Data<reqwest::Client>,
) -> error::Result<HttpResponse> {
    let linked_cards_response = client
        .get(format!("{}/carriers/v1.0/linked", env.lk_mosmetro_api_url))
        .bearer_auth(&query.access_token)
        .send()
        .await
        .map_err(error::ErrorBadGateway)?;

    is_success_response!(linked_cards_response);

    let linked_cards = linked_cards_response
        .json::<LinkedCardsResponse>()
        .await
        .map_err(|e| error::ErrorInternalServerError(format!("{:?}", e)))?;

    let mut response = Response::default();

    response.cards = linked_cards
        .data
        .cards
        .into_iter()
        .map(Into::into)
        .collect();

    response.waiting_link_cards = linked_cards
        .data
        .waiting_link_cards
        .into_iter()
        .map(Into::into)
        .collect();

    for card in response.cards.iter_mut() {
        card.operations =
            fetch_operations(client.clone(), &card.linked_card_id, &query.access_token).await?;
        card.trips = fetch_trips(client.clone(), &card.linked_card_id, &query.access_token).await?;
    }

    Ok(HttpResponse::Ok().json(response))
}

async fn fetch_operations(
    client: web::Data<reqwest::Client>,
    card_id: &String,
    access_token: &String,
) -> error::Result<Vec<Operation>> {
    let now = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap()
        .as_millis();

    // ,
    // "periodStartDateUtc": now,
    // "periodEndDateUtc": now - (30*24*60*60*1000)

    let operations_response = client
        .post("https://lk.mosmetro.ru/api/operations/v1.0?size=1&pageToken=")
        .bearer_auth(access_token)
        .json(&json!({
            "linkedCardIds": [card_id],
            "operationTypes": []
        }))
        .send()
        .await
        .map_err(error::ErrorInternalServerError)?;

    is_success_response!(operations_response);

    let operations = operations_response
        .json::<OperationsResponse>()
        .await
        .map_err(|e| error::ErrorInternalServerError(format!("{:?}", e)))?;

    Ok(operations.data.items.into_iter().map(Into::into).collect())
}

async fn fetch_trips(
    client: web::Data<reqwest::Client>,
    card_id: &String,
    access_token: &String,
) -> error::Result<Vec<Trip>> {
    let trips_response = client
        .get(format!(
            "https://lk.mosmetro.ru/api/trips/v1.0?size=1&pageToken=&linkedCardIds={card_id}"
        ))
        .bearer_auth(access_token)
        .send()
        .await
        .map_err(error::ErrorInternalServerError)?;

    let trips = trips_response
        .json::<TripsResponse>()
        .await
        .map_err(|e| error::ErrorInternalServerError(format!("{:?}", e)))?;

    Ok(trips.data.items.into_iter().map(Into::into).collect())
}

#[derive(Default, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Response {
    pub cards: Vec<Card>,
    pub waiting_link_cards: Vec<WaitingLinkCard>,
}

#[derive(Default, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Card {
    pub card_number: String,
    pub linked_card_id: String,
    pub card_type_name: String,
    pub display_name: String,
    pub card_type: String,
    pub status: String,
    pub balance: i32,
    pub unbalance: Option<i32>,
    pub tickets: Vec<Ticket>,
    pub untickets: Vec<DeferredAction>,
    pub operations: Vec<Operation>,
    pub trips: Vec<Trip>,
}

impl From<linked_cards::Card> for Card {
    fn from(card: linked_cards::Card) -> Self {
        let unbalance = card.deferred_actions.iter().fold(0, |acc, action| {
            if action.operation_name == "КОШЕЛЕК" {
                acc + action.sum as i32
            } else {
                acc
            }
        });

        Self {
            card_number: card
                .card
                .social_card_number
                .unwrap_or_else(|| card.card.card_number),
            card_type_name: card.card.card_type_name,
            display_name: card.card.display_name,
            card_type: card.card.card_type,
            linked_card_id: card.card.linked_card_id,
            status: card.status,
            balance: card.balance.balance.floor() as i32,
            unbalance: if unbalance > 0 { Some(unbalance) } else { None },
            untickets: card
                .deferred_actions
                .into_iter()
                .filter(|action| action.operation_name != "КОШЕЛЕК")
                .collect(),
            tickets: card.tickets,
            operations: Vec::new(),
            trips: Vec::new(),
        }
    }
}

#[derive(Default, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Operation {
    pub operation_name: String,
    pub date: i64,
    pub operation_type: String,
    pub payment: Option<Payment>,
    pub deferred_write: Option<DeferredWrite>,
    pub transfer: Option<Transfer>,
}

impl From<operations::Item> for Operation {
    fn from(value: operations::Item) -> Self {
        Self {
            operation_name: value.display_name,
            date: value.date,
            operation_type: value.operation_type,
            deferred_write: value.deferred_write,
            transfer: value.transfer,
            payment: value.payment,
        }
    }
}

#[derive(Default, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Trip {
    pub trip_name: String,
    pub trip_type: String,
    pub product_type_name: String,
    pub date: i64,
    pub is_face_pay: bool,
    pub sum: i32,
    pub kind: Option<String>,
    pub line_name: Option<String>,
}

impl From<trips::Item> for Trip {
    fn from(value: trips::Item) -> Self {
        Self {
            trip_name: value.display_name,
            trip_type: value.trip.trip_type,
            product_type_name: value.operation.type_name,
            date: value.trip.date,
            is_face_pay: value.trip.is_face_pay,
            sum: value.operation.sum as i32,
            kind: value.trip.ground_details.map(|details| details.kind),
            line_name: value
                .trip
                .metro_details
                .and_then(|details| details.lines.first().map(|line| line.name.clone())),
        }
    }
}

#[derive(Default, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct WaitingLinkCard {
    pub card_number: String,
    pub linked_card_id: String,
    pub card_uid: String,
    pub card_type: String,
    pub card_type_name: String,
    pub display_name: String,
    pub link_by_payment_state: LinkByPaymentState,
}

impl From<linked_cards::WaitingLinkCard> for WaitingLinkCard {
    fn from(value: linked_cards::WaitingLinkCard) -> Self {
        Self {
            card_number: value.card.card_number,
            linked_card_id: value.card.linked_card_id,
            card_uid: value.card.card_uid,
            card_type: value.card.card_type,
            card_type_name: value.card.card_type_name,
            display_name: value.card.display_name,
            link_by_payment_state: LinkByPaymentState {
                confirm_date_time_to_utc: value.link_by_payment_state.confirm_date_time_to_utc,
                confirm_sum: value.link_by_payment_state.confirm_sum as i32,
                status: value.link_by_payment_state.status,
            },
        }
    }
}

#[derive(Default, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LinkByPaymentState {
    pub confirm_date_time_to_utc: i64,
    pub confirm_sum: i32,
    pub status: String,
}
