import random

class CrowdSimulation:
    def __init__(self, graph):
        self.graph = graph
        self.node_counts = {n: 0 for n in graph.nodes()}
        self.history = []
        self.step_count = 0
        
    def step(self, entry_rate=100, movement_speed_multiplier=1.0):
        self.step_count += 1
        new_counts = {n: 0 for n in self.graph.nodes()}
        
        # Determine movement fractions based on speed
        stay_ratio_transit = max(0.1, 0.4 - 0.2 * movement_speed_multiplier)
        stay_ratio_facility = max(0.2, 0.6 - 0.2 * movement_speed_multiplier)
        exit_rate = min(0.9, 0.4 * movement_speed_multiplier)
        
        for n in self.graph.nodes():
            current = self.node_counts[n]
            if current == 0:
                continue
                
            node_type = self.graph.nodes[n]['type']
            
            if node_type == 'exit':
                leaving = int(current * exit_rate)
                new_counts[n] += (current - leaving)
                continue
                
            neighbors = list(self.graph.neighbors(n))
            if not neighbors:
                new_counts[n] += current
                continue
                
            stay_ratio = stay_ratio_facility if node_type in ['facility', 'destination'] else stay_ratio_transit
            staying = int(current * stay_ratio)
            moving = current - staying
            new_counts[n] += staying
            
            if moving > 0:
                # Prefer expanding towards exits or destinations
                # To simulate real movement, we weigh neighbors by their type / distance occasionally
                # For simplicity, distribute based on capacity
                caps = [self.graph.nodes[nbr]['capacity'] for nbr in neighbors]
                total_cap = sum(caps)
                if total_cap > 0:
                    probs = [c/total_cap for c in caps]
                else:
                    probs = [1/len(neighbors)]*len(neighbors)
                    
                # Distribute moving people
                for i in range(moving):
                    chosen = random.choices(neighbors, weights=probs, k=1)[0]
                    new_counts[chosen] += 1
                    
        # New arrivals
        entry_nodes = [n for n, attr in self.graph.nodes(data=True) if attr['type'] == 'entry']
        for n in entry_nodes:
            arrivals = int(entry_rate * (0.5 + random.random()))
            new_counts[n] += arrivals
            
        self.node_counts = new_counts
        
        # Save history for prediction
        self.history.append(self.node_counts.copy())
        if len(self.history) > 10:
            self.history.pop(0)

