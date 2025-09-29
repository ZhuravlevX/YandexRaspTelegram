use serde::{Deserialize};
pub mod mosmetro;
pub mod mostrans;

#[derive(Deserialize, Clone)]
pub struct Environment {
    #[serde(default = "default_host")]
    pub host: String,
    #[serde(default = "default_port")]
    pub port: u16,
    pub mosmetro_api_url: String,
    pub router_api_url: String,
    pub lk_mosmetro_api_url: String,
    pub moscowapp_api_url: String,
}

fn default_host() -> String {
    "127.0.0.1".to_string()
}

fn default_port() -> u16 {
    8080u16
}
