use crate::functions::getters::find_line_by_id;
use crate::types::schema::{Schema, Station};
use crate::types::StationMini;

pub mod getters;
pub mod updater;
pub mod route_time;
pub mod cache_cleaner;

pub fn convert_in_station_mini(station: &Station, schema: &Schema) -> StationMini {
    StationMini {
        id: station.id,
        name: station.name.ru.clone(),
        line_id: station.line_id,
        line_name: find_line_by_id(station.line_id, schema)
            .map(|l| l.name.ru.clone())
            .unwrap_or_default(),
    }
}