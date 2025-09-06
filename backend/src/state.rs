use crate::types::mosmetro::notifications::Notification;
use crate::types::mosmetro::router::RouterResponse;
use crate::types::mosmetro::schema::Schema;
use crate::types::mostrans::route::RouteDataResponse;
use crate::types::Environment;
use moka::future::Cache;
use parking_lot::RwLock;
use std::sync::Arc;
use std::time::Duration;

#[derive(Clone)]
pub struct AppState {
    pub schema: Arc<RwLock<Option<Schema>>>,
    pub notifications: Arc<RwLock<Option<Vec<Notification>>>>,
    pub route_cache: Cache<String, RouterResponse>,
    // pub route_cache: Arc<RwLock<HashMap<String, RouterResponse>>>,
    pub suggest_cache: Cache<String, RouteDataResponse>,
    pub env: Environment,
}

impl AppState {
    pub fn new(environment: Environment) -> Self {
        Self {
            schema: Arc::new(RwLock::new(None)),
            notifications: Arc::new(RwLock::new(None)),
            // route_cache: Arc::new(RwLock::new(HashMap::new())),
            route_cache: Cache::builder()
                .max_capacity(10000)
                .time_to_idle(Duration::from_secs(129600))
                .build(),
            suggest_cache: Cache::builder()
                .max_capacity(10000)
                .time_to_idle(Duration::from_secs(129600))
                .build(),
            env: environment,
        }
    }
}
