use serde::{Deserialize, Serialize};

pub type BoundsResponse = Vec<BoundsScooter>;

#[derive(Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BoundsScooter {
    pub id: String,
    pub lat: f64,
    pub lon: f64,
    pub map_icon: String,
    pub pin_icon: String,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Scooter {
    pub name: String,
    pub id: String,
    pub code: String,
    pub charge: Charge,
    pub lat: f64,
    pub lng: f64,
    pub remain_km: i64,
    pub minute_price: String,
    pub price: String,
    pub organisation: Organisation,
    // pub logo: String,
    // pub map_icon: String,
    // pub style: Style,
    // pub actions: Actions,
    // pub registration_form: Value,
    // pub registration_type: String,
    // pub messages: Vec<Value>,
    // pub price_offer_id: String,
    // pub booking: Value,
    // pub rent: Value,
    // pub rent_ending: Value,
    // pub rent_end: Value,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Charge {
    pub percent: i64,
    // pub color_icon: String,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Organisation {
    pub id: String,
    pub name: String,
    // pub alias: String,
    // pub email: Option<String>,
    // pub site: Option<String>,
    // pub telegram: Value,
    // pub features: Features,
    // pub logo: String,
    // pub insurance: Option<Insurance>,
    // pub user_registered: bool,
    // pub booking_payment: bool,
    // pub delimiter_color: String,
    // pub session_color: String,
    // pub header_color: String,
    // pub offer_signed: bool,
    // pub rent_header_color: String,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Features {
    pub booking: bool,
    pub booking_cancel: bool,
    pub rent: bool,
    pub promo_code_activation: bool,
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Insurance {
    pub price: i64,
    pub summary: String,
    pub more_details_link: String,
}

// #[derive(Debug, Serialize, Deserialize)]
// #[serde(rename_all = "camelCase")]
// pub struct Style {
//     pub header_color: String,
//     pub session_color: String,
//     pub delimiter_color: String,
//     pub rent_header_color: String,
//     pub profile_color: String,
//     pub navigation_color: String,
//     pub session_text_color: String,
//     pub booking_color: String,
// }

// #[derive(Debug, Serialize, Deserialize)]
// #[serde(rename_all = "camelCase")]
// pub struct Actions {
//     pub size: String,
//     pub items: Vec<Action>,
// }
//
// #[derive(Debug, Serialize, Deserialize)]
// #[serde(rename_all = "camelCase")]
// pub struct Action {
//     pub name: Option<String>,
//     #[serde(rename = "type")]
//     pub type_field: String,
//     pub background_color: String,
//     pub text_color: String,
//     pub icon: String,
//     // pub confirmation: Value,
//     pub link: Option<String>,
// }
