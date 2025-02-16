import folium
import pandas as pd
import branca.colormap as cm
from folium.plugins import HeatMap, Search
from folium import Popup
from folium.utilities import JsCode

# ---------------------------
# 1. data and initialization
# ---------------------------
df_final = pd.read_csv('data/filtered_census_data.csv')

# base map
map_obj = folium.Map(location=[53.7267, -127.6476], zoom_start=5, control_scale=True)

col65 = 'percent elderly 65+'
col85 = 'percent elderly 85+'

df_final = df_final.dropna(subset=['Latitude', 'Longitude', 'Geographic name', col65, col85])

vmin, vmax = 0, 40
colormap = cm.LinearColormap(colors=["#00BFFF", "#FF69B4"], vmin=vmin, vmax=vmax)
colormap.caption = "Percentage of Population Aged 65+"

# ---------------------------
# 2. heatmap layer
# ---------------------------
heat_data = [
    [row['Latitude'], row['Longitude'], min(max(row[col65], vmin), vmax)]
    for _, row in df_final.iterrows()
]
heatmap_layer = HeatMap(heat_data, radius=15, blur=10, name="Density")
heatmap_layer.add_to(map_obj)

# ---------------------------
# 3. population points layer
# ---------------------------
marker_group = folium.FeatureGroup(name="Data Points")
for _, row in df_final.iterrows():
    lat, lon = row['Latitude'], row['Longitude']
    p65, p85 = round(row[col65], 2), round(row[col85], 2)
    color = colormap(min(max(p65, vmin), vmax))
    
    marker = folium.CircleMarker(
        location=[lat, lon],
        radius=5,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        tooltip=folium.Tooltip(f"{row['Geographic name']}<br>65+: {p65}%<br>85+: {p85}%")
    )

    marker.options['percent65'] = p65
    marker.options['percent85'] = p85
    
    marker_group.add_child(marker)
marker_group.add_to(map_obj)

# ---------------------------
# 4. search functionality I
# ---------------------------
features = []
for _, row in df_final.iterrows():
    feature = {
        "type": "Feature",
        "properties": {
            "Geographic name": row["Geographic name"],
            "lat": row["Latitude"],
            "lon": row["Longitude"]
        },
        "geometry": {
            "type": "Point",
            "coordinates": [row["Longitude"], row["Latitude"]]
        }
    }
    features.append(feature)
geojson_data = {
    "type": "FeatureCollection",
    "features": features
}

invisible_marker_js = JsCode("""
    function(feature, latlng) {
        return L.marker(latlng, {
            icon: L.divIcon({
                html: "", 
                className: "invisible-icon", 
                iconSize: [0, 0]
            })
        });
    }
""")
geojson_layer = folium.GeoJson(
    geojson_data,
    name="Search Layer",
    point_to_layer=invisible_marker_js,
    control=False
)
geojson_layer.add_to(map_obj)

# ---------------------------
# 5. search functionality II
# ---------------------------
search = Search(
    layer=geojson_layer,
    search_label="Geographic name",
    placeholder="Search for a location",
    collapsed=False,
    search_zoom=12
).add_to(map_obj)

# ---------------------------
# 6. legend
# ---------------------------
colormap.add_to(map_obj)

# ---------------------------
# 7. healthcare facilities
# ---------------------------
df_healthcare = pd.read_csv('data/filtered_healthcare.csv')
healthcare_group = folium.FeatureGroup(name="Healthcare Facilities", show=False)

def get_facility_color(facility_type):
    facility_type = str(facility_type) if isinstance(facility_type, str) else ""
    if "Hospitals" in facility_type or "acute hospital" in facility_type:
        return "lightred"
    elif "Nursing" in facility_type or "Residential Care" in facility_type:
        return "lightblue"
    else:
        return "beige"

for _, row in df_healthcare.iterrows():
    name = row['facility_name']
    facility_type = row['odhf_facility_type']
    lat, lon = row['latitude'], row['longitude']
    icon = folium.Icon(icon="circle", prefix="fa", color=get_facility_color(facility_type))
    marker = folium.Marker(location=[lat, lon], icon=icon, tooltip=None)
    popup_content = f"<strong>{name}</strong><br>{facility_type}"
    marker.add_child(Popup(popup_content))
    healthcare_group.add_child(marker)
healthcare_group.add_to(map_obj)

# ---------------------------
# 8. layer control
# ---------------------------
folium.LayerControl(collapsed=True).add_to(map_obj)

# ---------------------------
# 9. sliders
# ---------------------------
# get names
map_id = map_obj.get_name()
mg_name = marker_group.get_name()

slider_html = f"""
<div id="slider65_container" style="position: fixed; bottom: 100px; left: 10px; z-index:9999; background: white; padding: 5px;">
  <label for="slider65">Age 65+ Minimum (%): </label>
  <input type="range" id="slider65" min="0" max="100" value="0" step="1">
  <span id="value65">0</span>
</div>
<div id="slider85_container" style="position: fixed; bottom: 50px; left: 10px; z-index:9999; background: white; padding: 5px;">
  <label for="slider85">Age 85+ Minimum (%): </label>
  <input type="range" id="slider85" min="0" max="100" value="0" step="1">
  <span id="value85">0</span>
</div>
<script>
document.addEventListener("DOMContentLoaded", function() {{
    // Ensure the slider elements exist.
    var slider65 = document.getElementById("slider65");
    var slider85 = document.getElementById("slider85");
    console.log("slider65 element:", slider65, "slider85 element:", slider85);

    var map_instance = {map_id};

    function updateMarkers() {{
      var threshold65 = parseFloat(slider65.value);
      var threshold85 = parseFloat(slider85.value);
      console.log("Slider 65+ value:", threshold65, "Slider 85+ value:", threshold85);
      document.getElementById("value65").innerHTML = threshold65;
      document.getElementById("value85").innerHTML = threshold85;
      {mg_name}.eachLayer(function(marker) {{
          var p65 = marker.options.percent65;
          var p85 = marker.options.percent85;
          // Log marker values for debugging.
          console.log("Marker:", marker, "p65:", p65, "p85:", p85);
          if (p65 >= threshold65 && p85 >= threshold85) {{
              if (!map_instance.hasLayer(marker)) {{
                  marker.addTo(map_instance);
              }}
          }} else {{
              if (map_instance.hasLayer(marker)) {{
                  map_instance.removeLayer(marker);
              }}
          }}
      }});
    }}

    slider65.addEventListener("input", updateMarkers);
    slider65.addEventListener("change", updateMarkers);
    slider85.addEventListener("input", updateMarkers);
    slider85.addEventListener("change", updateMarkers);
}});
</script>
"""

from folium import Element
map_obj.get_root().html.add_child(Element(slider_html))

# ---------------------------
# 10. save map
# ---------------------------
map_obj.save('map.html')
