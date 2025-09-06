use crate::types::mosmetro::schema::{Schema, Station};
use crate::types::mosmetro::StationMini;
use crate::utils::mosmetro::search::{find_connection_by_station_ids, find_line_by_id};

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

pub fn calculate_route_time(stations: Vec<usize>, schema: &Schema) -> u32 {
    let mut time: u32 = 0;
    for i in 0..stations.len() - 1 {
        time += find_connection_by_station_ids(stations[i], stations[i + 1], schema)
            .map(|c| c.path_length)
            .unwrap_or_default();
    }
    time
}
