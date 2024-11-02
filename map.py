import streamlit as st
import osmnx as ox
import networkx as nx
import folium
import geopandas as gpd

# Load hospital data
def load_hospital_data(file_path):
    geo_df = gpd.read_file(file_path)
    return geo_df

# Create a graph from the road network
def create_road_graph():
    place_name = "Pusad, Maharashtra, India"
    G = ox.graph_from_place(place_name, network_type='drive')
    return G

# Convert to a simple graph
G = nx.Graph(create_road_graph())

# Function to find k-shortest paths using Yen's algorithm
def find_k_shortest_paths(G, start_coords, end_coords, k=3):
    start_node = ox.distance.nearest_nodes(G, start_coords[1], start_coords[0])
    end_node = ox.distance.nearest_nodes(G, end_coords[1], end_coords[0])
    
    # Initialize the list to store the k shortest paths
    k_shortest_paths = []

    # Use Dijkstra for the shortest path as the initial path
    shortest_path = nx.shortest_path(G, start_node, end_node, weight='length')
    k_shortest_paths.append(shortest_path)
    
    # Iterate to find additional paths
    for i in range(1, k):
        # Temporary variable to hold the paths
        path_found = False
        
        # Create new paths based on the previous paths
        for j in range(len(k_shortest_paths[i - 1]) - 1):
            # Remove the edge from the current path
            edge_to_remove = (k_shortest_paths[i - 1][j], k_shortest_paths[i - 1][j + 1])
            G.remove_edge(*edge_to_remove)

            try:
                # Find a new path without the removed edge
                new_path = nx.shortest_path(G, start_node, end_node, weight='length')
                k_shortest_paths.append(new_path)
                path_found = True
            except nx.NetworkXNoPath:
                # If no path is found, simply continue
                continue
            
            # Restore the edge for further iterations
            G.add_edge(*edge_to_remove)

        # If no new paths were found, break early
        if not path_found:
            break

    return k_shortest_paths[:k]

# Create a map with the routes
def create_map(G, paths):
    folium_map = folium.Map(location=(G.nodes[paths[0][0]]['y'], G.nodes[paths[0][0]]['x']), zoom_start=14)
    
    for path in paths:
        path_nodes = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in path]
        folium.PolyLine(locations=path_nodes, color='blue', weight=5, opacity=0.7).add_to(folium_map)
        folium.Marker(location=path_nodes[0], popup='Start').add_to(folium_map)
        folium.Marker(location=path_nodes[-1], popup='End').add_to(folium_map)
    
    return folium_map

# Streamlit App
st.title("Road-Based K-Shortest Path Finder in Pusad")

# Load hospital data
hospital_data = load_hospital_data('pusad.geojson')

# Extract hospital names and coordinates
hospital_names = hospital_data['name'].tolist()
hospital_coords = {row['name']: (row['geometry'].y, row['geometry'].x) for _, row in hospital_data.iterrows()}

# Dropdown selection for hospitals
start_hospital = st.selectbox("Select Start Hospital", hospital_names)
end_hospital = st.selectbox("Select End Hospital", hospital_names)

# Find and display paths
if st.button("Find K-Shortest Paths"):
    start_coords = hospital_coords[start_hospital]
    end_coords = hospital_coords[end_hospital]
    
    k = 3  # Number of paths to return
    paths = find_k_shortest_paths(G, start_coords, end_coords, k)
    folium_map = create_map(G, paths)
    st.components.v1.html(folium_map._repr_html_(), height=600)
