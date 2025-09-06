use serde::{Deserialize, Serialize};

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct StopInfoResponse {
    pub id: String,
    pub name: String,
    #[serde(rename = "type")]
    pub stop_type: String,
    pub route_path: Vec<RoutePath>,
    // pub wifi: bool,
    // pub bench: Value,
    // pub elevator: Value,
    // pub comment: Vec<Value>,
    // pub hub: Vec<Value>,
    // pub photo: Value,
    // pub comment_total_count: i64,
    // pub color: String,
    // pub route_number: String,
    // pub is_favorite: bool,
    // pub share_url: String,
    // pub lat: f64,
    // pub lon: f64,
    // pub city_shuttle: bool,
    // pub electrobus: bool,
    // pub transport_types: Vec<String>,
    // pub route_name: Value,
    // pub shuttle_type: Value,
    // pub regional: bool,
    // pub test_mode: bool,
    // pub debug: Vec<Value>,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RoutePath {
    pub id: String,
    #[serde(rename = "type")]
    pub type_field: String,
    pub number: String,
    pub last_stop_name: String,
    // pub color: String,
    // pub font_color: String,
    pub city_shuttle: bool,
    pub sber_shuttle: bool,
    pub electrobus: bool,
    pub rate_url: Option<String>,
    pub external_forecast: Vec<ExternalForecast>,
    // pub external_forecast_time: Vec<Value>,
    // pub feature: Value,
    // pub is_favorite: bool,
    // pub messages: Vec<Value>,
}

#[derive(Default, Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ExternalForecast {
    pub time: i64,
    pub by_telemetry: i64,
    pub tm_id: i64,
    pub route_path_id: String,
}
