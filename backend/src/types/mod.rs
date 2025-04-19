use crate::types::notifications::Notification;
use crate::types::schema::Schema;
use parking_lot::RwLock;
use serde::{Deserialize, Serialize};
use std::sync::Arc;

pub mod schema;
pub mod notifications;
pub mod router;

#[derive(Clone)]
pub struct AppState {
    pub schema: Arc<RwLock<Option<Schema>>>,
    pub notifications: Arc<RwLock<Option<Vec<Notification>>>>,
    pub env: Environment,
}

impl AppState {
    pub fn new(environment: Environment) -> Self {
        Self {
            schema: Arc::new(RwLock::new(None)),
            notifications: Arc::new(RwLock::new(None)),
            env: environment,
        }
    }
}

#[derive(Serialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct StationMini {
    pub id: usize,
    pub name: String,
    pub line_id: usize,
    pub line_name: String,
}

#[derive(Deserialize, Clone)]
pub struct Environment {
    #[serde(default = "default_host")]
    pub host: String,
    #[serde(default = "default_port")]
    pub port: u16,
    pub mosmetro_api_url: String,
    pub router_api_url: String,
}

fn default_host() -> String {
    "127.0.0.1".to_string()
}

fn default_port() -> u16 {
    8080u16
}
