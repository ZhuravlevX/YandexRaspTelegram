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
    pub img: String,
}
