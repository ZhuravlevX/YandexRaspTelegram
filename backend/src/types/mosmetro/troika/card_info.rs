use serde::{Deserialize, Serialize};

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
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CardInfoCard {
    #[serde(default)]
    pub uid: String,
    pub card_number: String,
    pub display_name: String,
    #[serde(rename(deserialize = "limitedEditionName"))]
    pub limited: Option<String>,
    pub card_type: String,
    pub img: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AvailableProduct {
    pub id: String,
    pub name: String,
    pub descr: Option<String>,
    #[serde(rename(deserialize = "priceMin"))]
    pub price: f64,
}
