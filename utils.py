import networkx as nx
import numpy as np

def get_global_events():
    return {
        'MetLife Stadium (NY)': {'lat': 40.8128, 'lon': -74.0739, 'type': 'Sports'},
        'Wembley Stadium (London)': {'lat': 51.5560, 'lon': -0.2795, 'type': 'Concert'},
        'Tokyo Dome (Japan)': {'lat': 35.7056, 'lon': 139.7519, 'type': 'Convention'},
        'Wankhede Stadium (Mumbai)': {'lat': 18.9388, 'lon': 72.8258, 'type': 'Sports'}
    }

def create_venue_graph(event='MetLife Stadium (NY)'):
    """
    Creates a graph representing a large-scale event venue dynamically centered on a global location.
    Nodes represents zones (Entry, Food, Seats, Exits).
    Edges represent walkways between zones with an intrinsic distance weight.
    """
    G = nx.Graph()
    events = get_global_events()
    if event not in events:
        event = 'MetLife Stadium (NY)'
        
    base_lat = events[event]['lat']
    base_lon = events[event]['lon']
    
    lat_off = 0.001
    lon_off = 0.001
    
    # Define Nodes: ID and attributes (name, capacity, lat, lon, node_type)
    nodes_info = {
        'Gate_A': {'name': 'Entry Gate A', 'capacity': 500, 'lat': base_lat + lat_off, 'lon': base_lon - lon_off, 'type': 'entry'},
        'Gate_B': {'name': 'Entry Gate B', 'capacity': 500, 'lat': base_lat - lat_off, 'lon': base_lon - lon_off, 'type': 'entry'},
        'Main_Hall': {'name': 'Main Hall', 'capacity': 1000, 'lat': base_lat, 'lon': base_lon, 'type': 'transit'},
        'Food_Court_1': {'name': 'Food Court North', 'capacity': 300, 'lat': base_lat + lat_off/2, 'lon': base_lon + lon_off/2, 'type': 'facility'},
        'Food_Court_2': {'name': 'Food Court South', 'capacity': 300, 'lat': base_lat - lat_off/2, 'lon': base_lon + lon_off/2, 'type': 'facility'},
        'Merch_Stand': {'name': 'Merchandise', 'capacity': 150, 'lat': base_lat, 'lon': base_lon - lon_off/2, 'type': 'facility'},
        'Sec_1': {'name': 'Seating Section 1', 'capacity': 800, 'lat': base_lat + lat_off/2, 'lon': base_lon + lon_off, 'type': 'destination'},
        'Sec_2': {'name': 'Seating Section 2', 'capacity': 800, 'lat': base_lat, 'lon': base_lon + lon_off, 'type': 'destination'},
        'Sec_3': {'name': 'Seating Section 3', 'capacity': 800, 'lat': base_lat - lat_off/2, 'lon': base_lon + lon_off, 'type': 'destination'},
        'Exit_N': {'name': 'North Exit', 'capacity': 600, 'lat': base_lat + lat_off, 'lon': base_lon + lon_off*1.5, 'type': 'exit'},
        'Exit_S': {'name': 'South Exit', 'capacity': 600, 'lat': base_lat - lat_off, 'lon': base_lon + lon_off*1.5, 'type': 'exit'},
    }
    
    for node_id, attrs in nodes_info.items():
        G.add_node(node_id, **attrs)
        
    # Define Edges: (node1, node2, distance, base_capacity)
    edges_info = [
        ('Gate_A', 'Main_Hall', 30, 200),
        ('Gate_B', 'Main_Hall', 30, 200),
        ('Main_Hall', 'Food_Court_1', 20, 150),
        ('Main_Hall', 'Food_Court_2', 20, 150),
        ('Main_Hall', 'Merch_Stand', 10, 100),
        ('Food_Court_1', 'Sec_1', 25, 150),
        ('Food_Court_1', 'Sec_2', 30, 150),
        ('Food_Court_2', 'Sec_2', 30, 150),
        ('Food_Court_2', 'Sec_3', 25, 150),
        ('Merch_Stand', 'Sec_2', 20, 150),
        ('Sec_1', 'Exit_N', 15, 300),
        ('Sec_2', 'Exit_N', 30, 200),
        ('Sec_2', 'Exit_S', 30, 200),
        ('Sec_3', 'Exit_S', 15, 300),
    ]
    
    for u, v, dist, cap in edges_info:
        G.add_edge(u, v, distance=dist, capacity=cap)
        
    return G

def get_node_status(current_count, capacity):
    """
    Returns zone status based on capacity utilization.
    """
    ratio = current_count / capacity if capacity > 0 else 0
    if ratio < 0.4:
        return "Low", "green"
    elif ratio < 0.7:
        return "Medium", "yellow"
    elif ratio < 0.9:
        return "High", "orange"
    else:
        return "Critical", "red"
