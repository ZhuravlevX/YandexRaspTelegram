use serde::{Deserialize, Serialize};
use std::collections::HashMap;

// Важно! Закоменнтированные части присутствуют в ответе апишки, но не требуются для данного проекта

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct SchemaResponse {
    pub success: bool,
    pub data: Schema,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Schema {
    pub stations: Vec<Station>,
    pub lines: Vec<Line>,
    pub connections: Vec<Connection>,
    pub transitions: Vec<Transition>,
    // pub additional: Vec<Additional>,
    // pub width: i64,
    // pub height: i64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Connection {
    pub id: usize,
    pub perspective: bool,
    pub station_from_id: usize,
    pub station_to_id: usize,
    pub path_length: u32,
    pub bi: bool,
    // pub svg: String,
    // pub closed_backward: Option<serde_json::Value>,
    pub alternative: Option<bool>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Line {
    pub id: usize,
    pub perspective: bool,
    pub name: Name,
    // pub color: String,
    // pub icon: String,
    // pub ordering: usize,
    pub station_start_id: usize,
    pub station_end_id: usize,
    // pub text_start: Text,
    // pub text_end: Text,
    // pub neighboring_lines: Vec<Option<serde_json::Value>>,
    // pub alternative: Option<bool>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Station {
    pub id: usize,
    pub perspective: bool,
    pub name: Name,
    pub line_id: usize,
    pub location: Location,
    pub exits: Vec<Exit>,
    pub enter_time: Option<i64>,
    pub exit_time: Option<i64>,
    pub ordering: i64,
    pub mcd: Option<bool>,
    pub outside: Option<bool>,
    pub mcc: Option<bool>,
    pub history: Option<String>,
    pub audios: Vec<String>,
    pub schemes: Vec<String>,
    pub services: Vec<Service>,
    pub schedule_trains: HashMap<String, Vec<ScheduleTrain>>,
    pub work_time: Vec<WorkTime>,
    // pub accessibility_images: Vec<Option<serde_json::Value>>,
    // pub building_images: Vec<Option<serde_json::Value>>,
    // pub station_svg: StationSvg,
    // pub text_svg: Svg,
    // pub tap_svg: Svg,
    // pub alternative: Option<bool>,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Transition {
    pub id: usize,
    pub perspective: bool,
    pub station_from_id: usize,
    pub station_to_id: usize,
    pub path_length: i64,
    pub video_from: Option<String>,
    pub video_to: Option<String>,
    pub bi: bool,
    pub ground: bool,
    // pub svg: String,
    pub wagons: Vec<Wagon>,
    pub alternative: Option<bool>,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Exit {
    pub title: Name,
    pub exit_number: i64,
    pub location: Option<Location>,
    pub bus: Option<String>,
    pub trolleybus: Option<String>,
    pub tram: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Location {
    pub lat: f64,
    pub lon: f64,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Name {
    pub ru: String,
    pub en: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ScheduleTrain {
    pub station_to_id: i64,
    pub station_to_name: String,
    pub first: String,
    pub last: String,
    pub day_type: DayType,
    pub weekend: bool,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum DayType {
    Even,
    Odd,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Service {
    Bank,
    Battery,
    Candy,
    Carrier,
    Coffee,
    Elevator,
    Flowers,
    Food,
    GiftShop,
    Info,
    Invalid,
    Optics,
    Parking,
    Print,
    Sales,
    Theatre,
    Toilet,
    Vending,
    Window,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WorkTime {
    pub open: Option<String>,
    pub close: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Wagon {
    pub station_to_id: i64,
    pub station_prev_id: i64,
    pub types: Vec<Type>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum Type {
    All,
    Center,
    End,
    First,
    NearEnd,
    NearFirst,
}
