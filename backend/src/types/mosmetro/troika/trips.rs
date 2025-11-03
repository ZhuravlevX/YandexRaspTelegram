use serde::{Deserialize, Serialize};

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TripsResponse {
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
    pub trip: Trip,
    pub operation: Operation,
    // pub id: String,
    // pub payment_type: String,
    // pub card: Card,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Trip {
    pub date: i64,
    pub ground_details: Option<GroundDetails>,
    pub metro_details: Option<MetroDetails>,
    pub is_face_pay: bool,
    #[serde(rename = "type")]
    pub trip_type: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct GroundDetails {
    pub kind: String,
    // pub id: String,
    // pub route_id: String,
    // pub icon: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct MetroDetails {
    pub lines: Vec<Line>,
    // pub id: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Line {
    pub name: String,
    // pub id: String,
    // pub icon: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Operation {
    pub sum: f64,
    pub type_name: String,
    // pub id: String,
    // pub trip_count: i64,
    // #[serde(rename = "type")]
    // pub type_field: String,
    // pub type_id: String,
    // pub icon: String,
}

// #[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
// #[serde(rename_all = "camelCase")]
// pub struct Card {
//     pub card_number: String,
//     pub social_card_number: Option<String>,
//     pub display_name: String,
//     pub limited: bool,
//     pub card_type: String,
//     pub card_type_name: String,
//     pub icon: String,
//     pub img: String,
//     pub linked_card_id: String,
// }
