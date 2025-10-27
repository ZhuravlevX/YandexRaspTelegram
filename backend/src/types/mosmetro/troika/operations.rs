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
    pub date: i32,
    pub payment: Payment,
    // pub id: String,
    // #[serde(rename = "type")]
    // pub type_field: String,
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
    pub receipt_url: String,
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
