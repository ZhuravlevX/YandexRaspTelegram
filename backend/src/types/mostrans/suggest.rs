use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Clone)]
pub struct SuggestData {
    pub id: String,
    pub name: String,
    pub description: String,
    pub route_number: String,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SuggestResponse {
    pub data: Vec<Data>,
    // pub page: i64,
    // #[serde(rename = "perPage")]
    // pub per_page: i64,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Data {
    pub id: String,
    pub name: String,
    pub description: String,
    pub route: Route,
    // #[serde(rename = "type")]
    // pub type_field: String,
    // pub location: Value,
    // pub distance: Value,
    // pub icon: String,
    // pub highlight: Vec<Value>,
    // pub group: bool,
    // #[serde(default)]
    // pub items: Vec<Item>,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Route {
    pub number: String,
    // pub color: String,
    // #[serde(rename = "fontColor")]
    // pub font_color: String,
}

// #[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
// pub struct Item {
//     pub id: String,
//     #[serde(rename = "type")]
//     pub type_field: String,
//     pub name: String,
//     pub location: Value,
//     pub description: String,
//     pub distance: Value,
//     pub icon: String,
//     pub highlight: Vec<Value>,
//     pub group: bool,
//     pub route: Route2,
// }
