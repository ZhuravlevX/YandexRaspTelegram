use serde::{Deserialize, Serialize};

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LinkedCardsResponse {
    pub data: Data,
    pub success: bool,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Data {
    pub cards: Vec<Card>,
    pub waiting_link_cards: Vec<WaitingLinkCard>,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Card {
    pub card: CardInfo,
    pub status: String,
    pub balance: Balance,
    pub tickets: Vec<Ticket>,
    pub deferred_actions: Vec<DeferredAction>,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CardInfo {
    pub card_number: String,
    pub social_card_number: Option<String>,
    pub limited: bool,
    pub limited_edition_name: Option<String>,
    pub linked_card_id: String,
    pub card_type_name: String,
    pub display_name: String,
    pub card_type: String,
    pub img: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Balance {
    pub date: i64,
    pub balance: f64,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DeferredAction {
    pub operation_name: String,
    pub sum: f64,
    pub date: i64,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WaitingLinkCard {
    pub card: WaitingLinkCardCard,
    pub current_link_type: String,
    pub possible_link_types: Vec<String>,
    pub link_by_payment_state: LinkByPaymentState,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WaitingLinkCardCard {
    pub card_number: String,
    pub card_uid: String,
    pub display_name: String,
    pub limited: bool,
    pub card_type: String,
    pub card_type_name: String,
    pub icon: String,
    pub img: String,
    pub linked_card_id: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct LinkByPaymentState {
    pub confirm_date_time_to_utc: i64,
    pub confirm_sum: f64,
    pub status: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Ticket {
    pub ticket_name: String,
    pub remain_day_count: i32,
    pub product_id: String,
    pub is_active: bool,
    pub total_days_count: i32,
}
