use serde::{Serialize, Deserialize};

#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct RouterResponse {
    pub data: Vec<Variant>,
}

#[derive(Debug, Clone, PartialEq, Deserialize)]
pub struct Variant {
    pub nodes: Vec<usize>,
    pub time: u32,
    pub transfers: u32,
}

#[derive(Serialize)]
pub struct RouterRequest {
    pub from: usize,
    pub to: usize,
}