use serde::Serialize;

pub mod notifications;
pub mod schema;
pub mod router;
pub mod troika;

#[derive(Serialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct StationMini {
    pub id: usize,
    pub name: String,
    pub line_id: usize,
    pub line_name: String,
}