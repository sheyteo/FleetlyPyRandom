import folium

# Define boundaries
latMax = 48.165312
latMin = 48.113
longMax = 11.6467088
longMin = 11.50302

# Calculate the center of the rectangle for initial map location
center_lat = (latMax + latMin) / 2
center_long = (longMax + longMin) / 2

# Create a map centered at the midpoint
m = folium.Map(location=[center_lat, center_long], zoom_start=14)

# Define points to plot (example points within boundaries)
points = [
    (48.165312, 11.6467088),
    (48.113, 11.50302),
]

#for lat, long in points:
        #folium.Marker(location=[lat, long], popup=f"Point: {lat}, {long}").add_to(m)

# Save map to an HTML file
m.save("map.html")

print("Map created and saved as 'map.html'. Open this file in your browser to view it.")
