import networkx as nx

def calculate_weight(u, v, d, G, node_counts):
    """
    Calculate dynamic edge weight based on base distance and destination node congestion.
    """
    base_dist = d['distance']
    dest_count = node_counts.get(v, 0)
    dest_capacity = G.nodes[v]['capacity']
    
    ratio = dest_count / dest_capacity if dest_capacity > 0 else 1.0
    penalty = 1.0
    if ratio > 0.9:
        penalty = 10.0
    elif ratio > 0.7:
        penalty = 3.0
    elif ratio > 0.4:
        penalty = 1.5
        
    return base_dist * penalty

def find_best_route(G, node_counts, source, target):
    """
    Finds the optimal path between source and target taking actual congestion into account.
    """
    try:
        path = nx.shortest_path(G, source=source, target=target, 
                                weight=lambda u, v, d: calculate_weight(u, v, d, G, node_counts))
        return path
    except nx.NetworkXNoPath:
        return None
