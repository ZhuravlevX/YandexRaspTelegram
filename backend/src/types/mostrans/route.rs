use serde::{Deserialize, Serialize};

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RouteDataResponse {
    pub id: String,
    pub number: String,
    #[serde(rename = "type")]
    pub transport_type: String,
    // pub color: String,
    // pub font_color: String,
    // pub name: Value,
    // pub city_shuttle: bool,
    // pub shuttle_type: Value,
    // pub electrobus: bool,
    // pub icon: Value,
    pub directions: Vec<Direction>,
    // pub is_favorite: bool,
    // pub regional: bool,
    // pub test_mode: bool,
    pub contractor: String,
    // pub messages: Vec<Value>,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Direction {
    pub first_stop_name: String,
    pub last_stop_name: String,
    pub route_paths: Vec<RoutePath>,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RoutePath {
    pub id: String,
    // pub encoded_polyline: String,
    pub stops: Vec<Stop>,
    pub end_stop_name: String,
    pub line_color: String,
    pub line_transparent: bool,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Stop {
    pub id: String,
    pub num: i64,
    pub name: String,
    pub lat: f64,
    pub lon: f64,
}
