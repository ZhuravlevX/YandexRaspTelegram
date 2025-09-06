use crate::types::mosmetro::schema::{Connection, Line, Schema, Station, Transition};

pub fn find_station_by_id(id: usize, schema: &Schema) -> Option<&Station> {
    schema.stations.iter().find(|&s| s.id == id)
}

pub fn find_line_by_id(id: usize, schema: &Schema) -> Option<&Line> {
    schema.lines.iter().find(|&l| l.id == id)
}

#[allow(dead_code)]
pub fn find_transition_by_station_ids(
    from: usize,
    to: usize,
    schema: &Schema,
) -> Option<&Transition> {
    schema.transitions.iter().find(|&t| {
        (t.station_from_id == from && t.station_to_id == to)
            || (t.station_from_id == to && t.station_to_id == from)
    })
}

pub fn find_connection_by_station_ids(
    from: usize,
    to: usize,
    schema: &Schema,
) -> Option<&Connection> {
    schema.connections.iter().find(|&c| {
        (c.station_from_id == from && c.station_to_id == to)
            || (c.station_from_id == to && c.station_to_id == from)
    })
}
