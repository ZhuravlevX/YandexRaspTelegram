use serde::{Deserialize, Serialize};

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct OperationsResponse {
    pub data: Data,
    pub success: bool,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Data {
    pub items: Vec<Item>,
    // pub next_page_token: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Item {
    pub display_name: String,
    pub status: String,
    pub date: i64,
    #[serde(rename = "type")]
    pub operation_type: String,
    pub payment: Option<Payment>,
    pub deferred_write: Option<DeferredWrite>,
    pub transfer: Option<Transfer>,
    // pub id: String,
    // pub card: Card,
}

// #[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
// #[serde(rename_all = "camelCase")]
// pub struct Card {
//     pub card_number: String,
//     pub display_name: String,
//     pub limited: bool,
//     pub limited_edition_name: String,
//     pub card_type: String,
//     pub card_type_name: String,
//     pub icon: String,
//     pub img: String,
//     pub linked_card_id: String,
// }

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Payment {
    pub sum: f64,
    pub receipt_url: Option<String>,
    pub product: Product,
    // pub income: bool,
    // pub source_type: String,
    // pub source_payment_type: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Product {
    pub product_id: String,
    pub product_name: String,
    // pub product_type: String,
    // pub icon: String,
    // pub img: String,
    // pub wallet: bool,
    // pub vtb_product_id: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Transfer {
    pub product: Product,
    pub balance: f64,
    pub destination_card: DestinationCard,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DestinationCard {
    pub card_number: String,
    pub display_name: String,
    pub limited: bool,
    pub card_type: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DeferredWrite {
    pub sum: f64,
    pub card_balance: f64,
    pub product: Product2,
    pub device_type_name: String,
    pub device_type_id: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Product2 {
    pub product_id: String,
    pub product_type: String,
    pub product_name: String,
    pub icon: String,
    pub img: String,
    pub wallet: bool,
    pub vtb_product_id: String,
}
