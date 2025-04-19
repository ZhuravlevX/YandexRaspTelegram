use crate::functions::getters::find_connection_by_station_ids;
use crate::types::schema::Schema;

pub fn calc_route_time(stations: Vec<usize>, schema: &Schema) -> u32 {
    let mut time: u32 = 0;
    for i in 0..stations.len() - 1 {
        time += find_connection_by_station_ids(stations[i], stations[i + 1], schema)
            .map(|c| c.path_length)
            .unwrap_or_default();
    }
    time
}
