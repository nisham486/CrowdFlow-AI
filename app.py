import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

from utils import create_venue_graph, get_node_status, get_global_events
from simulation import CrowdSimulation
from routing import find_best_route
from prediction import predict_future_congestion

st.set_page_config(page_title="CrowdFlow AI", layout="wide", page_icon="🏟️")

st.markdown("""
    <style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .metric-card {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        border-left: 5px solid #00E676;
    }
    .metric-card-high {
        border-left: 5px solid #FF3D00;
    }
    </style>
""", unsafe_allow_html=True)

# Geocoder setup
@st.cache_data
def get_coordinates(location_name):
    try:
        geolocator = Nominatim(user_agent="crowdflow_ai_bot")
        location = geolocator.geocode(location_name)
        if location:
            return location.latitude, location.longitude
    except Exception:
        pass
    return None, None

# Initialize Session State
if 'current_event' not in st.session_state:
    st.session_state.current_event = 'MetLife Stadium (NY)'
    st.session_state.graph = create_venue_graph(st.session_state.current_event)
    st.session_state.sim = CrowdSimulation(st.session_state.graph)
    st.session_state.running = False
    st.session_state.route_source = 'Gate_A'
    st.session_state.route_target = 'Exit_N'

st.sidebar.title("🎛️ App Mode")
app_mode = st.sidebar.radio("Select View:", ["🌍 Global Tracker", "🏟️ Venue Simulation"])

st.sidebar.markdown("---")

if app_mode == "🌍 Global Tracker":
    st.title("🌍 Global Crowd Events Tracker")
    st.write("View major crowd events happening globally and see how far they are from your current location.")
    
    st.sidebar.markdown("### 📍 Your Location")
    user_location = st.sidebar.text_input("Enter City, Country (e.g. Mumbai, India)", "New Delhi, India")
    
    user_lat, user_lon = get_coordinates(user_location)
    
    events = get_global_events()
    event_names = list(events.keys())
    lats = [events[e]['lat'] for e in event_names]
    lons = [events[e]['lon'] for e in event_names]
    types = [events[e]['type'] for e in event_names]
    
    # Plotly Global Map
    map_data = []
    
    # Event Markers
    map_data.append(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='markers+text',
        marker=dict(size=15, color='#FF3D00', symbol='circle'),
        text=event_names,
        textposition="top right",
        hoverinfo='text',
        name='Live Events'
    ))
    
    # User Marker
    if user_lat and user_lon:
        map_data.append(go.Scattermapbox(
            lat=[user_lat],
            lon=[user_lon],
            mode='markers+text',
            marker=dict(size=20, color='#00E676', symbol='star'),
            text=["Your Location"],
            textposition="bottom center",
            hoverinfo='text',
            name='You'
        ))
    
    # Set center map
    center_lat = user_lat if user_lat else 20.0
    center_lon = user_lon if user_lon else 0.0

    fig = go.Figure(data=map_data,
        layout=go.Layout(
            mapbox_style="carto-darkmatter",
            mapbox_center={"lat": center_lat, "lon": center_lon},
            mapbox_zoom=2,
            margin={"r":0,"t":0,"l":0,"b":0},
            height=600,
            showlegend=True
        ))
        
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("💡 To view live crowd flow inside one of these events, switch to the 'Venue Simulation' mode and select the event!")

elif app_mode == "🏟️ Venue Simulation":
    st.title("🏟️ Event Predictive Navigation")
    
    # Event Selector
    events = get_global_events()
    selected_event = st.sidebar.selectbox("Select Global Event", list(events.keys()), index=list(events.keys()).index(st.session_state.current_event))
    
    if selected_event != st.session_state.current_event:
        st.session_state.current_event = selected_event
        st.session_state.graph = create_venue_graph(selected_event)
        st.session_state.sim = CrowdSimulation(st.session_state.graph)
        # Refresh screen to apply state immediately safely
        st.rerun()

    st.sidebar.markdown("### Controls")
    run_col1, run_col2 = st.sidebar.columns(2)
    if run_col1.button("▶️ Step / Run"):
        st.session_state.running = True
        st.session_state.sim.step(
            entry_rate=st.session_state.get('entry_rate', 100),
            movement_speed_multiplier=st.session_state.get('speed', 1.0)
        )
    if run_col2.button("⏹️ Pause"):
        st.session_state.running = False
    if st.sidebar.button("🔄 Reset Crowd"):
        st.session_state.sim = CrowdSimulation(st.session_state.graph)

    st.sidebar.markdown("### Simulation Parameters")
    entry_rate = st.sidebar.slider("Entry Rate (people/step)", 10, 500, 100, key='entry_rate')
    speed = st.sidebar.slider("Movement Speed", 0.5, 2.0, 1.0, 0.1, key='speed')

    st.sidebar.markdown("### Routing Target")
    zones = list(st.session_state.graph.nodes())
    
    # Ensure sources and targets are in current bounds 
    if st.session_state.route_source not in zones:
        st.session_state.route_source = zones[0]
    if st.session_state.route_target not in zones:
        st.session_state.route_target = zones[-1]
        
    src_idx = zones.index(st.session_state.route_source) 
    tgt_idx = zones.index(st.session_state.route_target)

    st.session_state.route_source = st.sidebar.selectbox("Start Zone", zones, index=src_idx, format_func=lambda x: st.session_state.graph.nodes[x]['name'])
    st.session_state.route_target = st.sidebar.selectbox("Destination Zone", zones, index=tgt_idx, format_func=lambda x: st.session_state.graph.nodes[x]['name'])

    col1, col2 = st.columns([2, 1])

    best_path = find_best_route(st.session_state.graph, st.session_state.sim.node_counts, 
                                st.session_state.route_source, st.session_state.route_target)

    predictions, risks = predict_future_congestion(st.session_state.sim.history, st.session_state.graph, steps_ahead=3)

    with col1:
        st.subheader(f"Live Heatmap & Routing: {st.session_state.current_event}")
        
        G = st.session_state.graph
        
        edge_lat = []
        edge_lon = []
        for edge in G.edges():
            lat0, lon0 = G.nodes[edge[0]]['lat'], G.nodes[edge[0]]['lon']
            lat1, lon1 = G.nodes[edge[1]]['lat'], G.nodes[edge[1]]['lon']
            edge_lat.extend([lat0, lat1, None])
            edge_lon.extend([lon0, lon1, None])

        edge_trace = go.Scattermapbox(
            lat=edge_lat, lon=edge_lon,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines')

        path_lat = []
        path_lon = []
        if best_path:
            for i in range(len(best_path)-1):
                lat0, lon0 = G.nodes[best_path[i]]['lat'], G.nodes[best_path[i]]['lon']
                lat1, lon1 = G.nodes[best_path[i+1]]['lat'], G.nodes[best_path[i+1]]['lon']
                path_lat.extend([lat0, lat1, None])
                path_lon.extend([lon0, lon1, None])
                
        path_trace = go.Scattermapbox(
            lat=path_lat, lon=path_lon,
            line=dict(width=4, color='#00E676'),
            hoverinfo='none',
            mode='lines')
            
        node_lat = []
        node_lon = []
        node_text = []
        node_color = []
        node_size = []
        
        for node in G.nodes():
            node_lat.append(G.nodes[node]['lat'])
            node_lon.append(G.nodes[node]['lon'])
            
            count = st.session_state.sim.node_counts[node]
            cap = G.nodes[node]['capacity']
            status, color = get_node_status(count, cap)
            
            node_text.append(f"{G.nodes[node]['name']}<br>People: {count}/{cap}<br>Status: {status}")
            
            if color == 'green': hex_col = '#00E676'
            elif color == 'yellow': hex_col = '#FFEA00'
            elif color == 'orange': hex_col = '#FF9100'
            else: hex_col = '#FF1744'
            node_color.append(hex_col)
            
            size = min(30, max(10, (count/cap)*30 + 10)) if cap > 0 else 10
            node_size.append(size)

        node_trace = go.Scattermapbox(
            lat=node_lat, lon=node_lon,
            mode='markers+text',
            text=[G.nodes[n]['name'] for n in G.nodes()],
            textposition="top center",
            hoverinfo='text',
            hovertext=node_text,
            marker=dict(
                color=node_color,
                size=node_size))

        # Center Map tightly on the current venue based on its coordinates
        event_base_lat = events[st.session_state.current_event]['lat']
        event_base_lon = events[st.session_state.current_event]['lon']

        fig = go.Figure(data=[edge_trace, path_trace, node_trace],
                     layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0,l=0,r=0,t=0),
                        mapbox=dict(
                            style="carto-darkmatter",
                            center=dict(lat=event_base_lat, lon=event_base_lon),
                            zoom=16
                        ),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        height=600
                     ))
        
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🧠 AI Insights & Path")
        
        st.markdown("#### Smart Routing")
        if best_path:
            route_names = [G.nodes[n]['name'] for n in best_path]
            st.info(" → ".join(route_names))
        else:
            st.warning("No path found.")
            
        st.markdown("#### Congestion Predictions")
        alerts = []
        for node, risk in risks.items():
            if "High" in risk or "Critical" in risk:
                alerts.append({'Zone': G.nodes[node]['name'], 'Warning': risk, 'Predicted': predictions[node][-1]})
                
        if alerts:
            db = pd.DataFrame(alerts)
            for _, row in db.iterrows():
                if "Critical" in row['Warning']:
                    st.error(f"**{row['Zone']}**: {row['Warning']} (Pred: {row['Predicted']} people)")
                else:
                    st.warning(f"**{row['Zone']}**: {row['Warning']} (Pred: {row['Predicted']} people)")
        else:
            st.success("All zones operating within safe limits.")
            
        # Metrics
        st.markdown("#### Live Stats")
        total_people = sum(st.session_state.sim.node_counts.values())
        st.metric("Total People in Venue", total_people)
        st.metric("Simulation Step", st.session_state.sim.step_count)
