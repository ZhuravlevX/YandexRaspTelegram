use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NotificationsResponse {
    pub success: bool,
    pub data: Vec<Notification>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Notification {
    pub id: usize,
    pub title: Description,
    pub description: Description,
    pub start_date: String,
    pub end_date: String,
    pub hidden_end_date: bool,
    pub stations: Vec<Station>,
    pub lines: Vec<Line>,
    // pub connections: Vec<Option<serde_json::Value>>,
    // pub transitions: Vec<Option<serde_json::Value>>,
    // pub alternative_lines: Vec<Option<serde_json::Value>>,
    // pub alternative_stations: Vec<Option<serde_json::Value>>,
    // pub alternative_connections: Vec<Option<serde_json::Value>>,
    // pub alternative_transitions: Vec<Option<serde_json::Value>>,
    pub extra_svg: Option<String>,
    pub url: Option<String>,
}


#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Line {
    pub id: usize,
    pub name: String,
    pub icon: String,
    pub ordering: i64,
    pub all_stations_closed: bool,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Station {
    pub station_id: usize,
    pub title: Description,
    pub description: Description,
    pub status: Status,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Description {
    pub ru: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum Status {
    Emergency,
}
