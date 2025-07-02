import pandas as pd
import os

def get_stop_name(stop_id, stops_df):
    row = stops_df[stops_df['stop_id'] == stop_id]
    if not row.empty:
        return row.iloc[0]['stop_name']
    return None

def get_stop_types(stop_id, stop_times_df, trips_df, routes_df):
    trip_ids = stop_times_df[stop_times_df['stop_id'] == stop_id]['trip_id'].unique()
    route_types = set()
    for trip_id in trip_ids:
        route_row = trips_df[trips_df['trip_id'] == trip_id]
        if not route_row.empty:
            route_id = route_row.iloc[0]['route_id']
            route_type_row = routes_df[routes_df['route_id'] == route_id]
            if not route_type_row.empty:
                route_type = route_type_row.iloc[0]['route_type']
                route_types.add(route_type)
    return route_types if route_types else {'?'}

def main():
    gtfs_dir = os.path.join(os.path.dirname(__file__), '../data/gtfs')
    transfers = pd.read_csv(os.path.join(gtfs_dir, 'transfers.txt'), dtype=str)
    stops = pd.read_csv(os.path.join(gtfs_dir, 'stops.txt'), dtype=str)
    stop_times = pd.read_csv(os.path.join(gtfs_dir, 'stop_times.txt'), dtype=str)
    trips = pd.read_csv(os.path.join(gtfs_dir, 'trips.txt'), dtype=str)
    routes = pd.read_csv(os.path.join(gtfs_dir, 'routes.txt'), dtype=str)

    # Stop_ids pour Porte Dauphine et Gare du Nord (à ajuster si besoin)
    porte_dauphine_ids = stops[stops['stop_name'].str.contains('Porte Dauphine', case=False, na=False)]['stop_id'].tolist()
    gare_du_nord_ids = stops[stops['stop_name'].str.contains('Gare du Nord', case=False, na=False)]['stop_id'].tolist()

    def print_links(station_name, ids):
        print(f'\n--- Transfers pour {station_name} ---')
        links = set()
        for stop_id in ids:
            # Transfers où ce stop est from ou to
            rel = transfers[(transfers['from_stop_id'] == stop_id) | (transfers['to_stop_id'] == stop_id)]
            for _, row in rel.iterrows():
                if row['from_stop_id'] == stop_id:
                    other = row['to_stop_id']
                else:
                    other = row['from_stop_id']
                links.add(other)
        for other_id in links:
            name = get_stop_name(other_id, stops)
            types = get_stop_types(other_id, stop_times, trips, routes)
            print(f"{other_id}: {name} | types: {types}")

    print_links('Porte Dauphine', porte_dauphine_ids)
    print_links('Gare du Nord', gare_du_nord_ids)

if __name__ == '__main__':
    main() 