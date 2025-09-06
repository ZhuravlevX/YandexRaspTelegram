use crate::state::AppState;
use actix_web::rt::time;
use log::info;
use std::sync::Arc;
use std::time::Duration;

static CLEAN_TIMEOUT: Duration = Duration::from_secs(36 * 3600);
// TODO Remove this
pub async fn cache_cleaner(state: Arc<AppState>) {
    let mut interval = time::interval(CLEAN_TIMEOUT);
    loop {
        interval.tick().await;
        // state.route_cache.write().clear();
        info!("Cache successfully cleaned");
    }
}
