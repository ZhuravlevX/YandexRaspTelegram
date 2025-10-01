use serde::{Deserialize, Serialize};

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CardSearchResponse {
    pub cards: Vec<CardSearchCard>,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CardSearchCard {
    pub number: String,
    pub uid: String,
    pub type_id: String,
    pub limited: bool,
    pub limited_edition_name: Option<String>,
    // pub type_name: String,
    // pub cms_name: String,
    // pub cms_title: String,
    // pub icon: String,
    pub img: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CardInfoResponse {
    pub data: CardInfoData,
    pub success: bool,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CardInfoData {
    pub card: CardInfoCard,
    pub available_products: Vec<AvailableProduct>,
    // pub available_wallet: AvailableWallet,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CardInfoCard {
    pub card_number: String,
    pub display_name: String,
    #[serde(rename(deserialize = "limitedEditionName"))]
    pub limited: Option<String>,
    pub card_type: String,
    // pub icon: String,
    pub img: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AvailableProduct {
    pub name: String,
    pub descr: String,
    #[serde(rename(deserialize = "priceMin"))]
    pub price: f64,
    // pub id: String,
    // pub type_name: String,
    // pub type_id: String,
    // pub price_max: f64,
    // pub sale_type: String,
    // pub payment_types: Vec<String>,
    // pub ticket_type: String,
    // pub promo: bool,
}

// #[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
// #[serde(rename_all = "camelCase")]
// pub struct AvailableWallet {
//     pub id: String,
//     pub name: String,
//     pub descr: String,
//     pub type_name: String,
//     pub type_id: String,
//     pub price_min: f64,
//     pub price_max: f64,
//     pub sale_type: String,
//     pub payment_types: Vec<String>,
//     pub promo: bool,
// }
