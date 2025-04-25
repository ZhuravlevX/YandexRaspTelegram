use crate::types::{notifications::NotificationsResponse, schema::SchemaResponse, AppState};
use actix_web::rt::time::{interval, sleep};
use log::{error, info, warn};
use serde::de::DeserializeOwned;
use std::sync::Arc;
use std::time::Duration;

static TIMEOUT: Duration = Duration::from_secs(30);
static UPDATE_TIMEOUT: Duration = Duration::from_secs(3600);

pub async fn updater(state: Arc<AppState>, api_url: String) {
    let client = awc::Client::new();

    let mut interval = interval(UPDATE_TIMEOUT);
    loop {
        interval.tick().await;
        update_data(&state, &api_url, &client).await;
    }
}

async fn update_data(state: &Arc<AppState>, api_url: &String, client: &awc::Client) {
    // update schema
    let schema: SchemaResponse = fetch_data(format!("{api_url}/schema/v1.0"), &client).await;
    *state.schema.write() = Some(schema.data);
    info!("Schema successfully updated");

    // update notifications
    let notifications: NotificationsResponse =
        fetch_data(format!("{api_url}/notifications/v2"), &client).await;
    *state.notifications.write() = Some(notifications.data);
    info!("Notifications successfully updated");

    sleep(UPDATE_TIMEOUT).await;
}

async fn fetch_data<T: DeserializeOwned>(url: String, client: &awc::Client) -> T {
    loop {
        let res = client
            .get(&url)
            .insert_header((
                "User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
            ))
            .send()
            .await;

        match res {
            Ok(mut res) => {
                if res.status().is_success() {
                    return res.json::<T>().limit(20_000_000).await.unwrap();
                } else {
                    warn!(
                        "Can`t fetch data from {}. Retry in {}s",
                        url,
                        TIMEOUT.as_secs()
                    );
                }
            }
            Err(e) => {
                error!("Error fetching data from {}: {}", url, e);
            }
        }

        sleep(TIMEOUT).await;
    }
}
