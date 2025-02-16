import folium
import pandas as pd
import branca.colormap as cm
from folium.plugins import HeatMap, Search
from folium import Popup, Element
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
# 3. data population points layer
# ---------------------------
# slider = 0 (present)
marker_group = folium.FeatureGroup(name="Actual Data (Year 0)", control=False)
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
Search(
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
# 7. healthcare facilities layer
# ---------------------------
df_healthcare = pd.read_csv('data/filtered_healthcare.csv')

healthcare_group = folium.FeatureGroup(name="Healthcare Facilities", show=False, control=True)

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
# 8. predicted data layers (years 1-10)
# ---------------------------
pred_group_names = []
for year in range(1, 11):
    filename = f'data/predicted_census_data_{year}.csv'
    df_predictions = pd.read_csv(filename)
    df_pred = pd.merge(df_predictions, df_final[['Geographic name', col65]], on='Geographic name', how='left')
    pred_group = folium.FeatureGroup(name=f"Predicted Aging Population ({year} years)", control=False)
    for _, row in df_pred.iterrows():
        lat, lon = row['Latitude'], row['Longitude']
        actual_p65 = round(row[col65], 2)  # actual value from current data
        p65_pred = round(row['predicted 65+'], 2)
        p85_pred = round(row['predicted 85+'], 2)
        color = colormap(min(max(p65_pred, vmin), vmax))
        tooltip_text = (
            f"{row['Geographic name']}<br>"
            f"Predicted 65+: {p65_pred}%<br>"
            f"Predicted 85+: {p85_pred}%"
        )
        marker = folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            tooltip=folium.Tooltip(tooltip_text)
        )

        marker.options['predicted65'] = p65_pred
        marker.options['predicted85'] = p85_pred
        marker.options['actual65'] = actual_p65
        pred_group.add_child(marker)
    pred_group.add_to(map_obj)
    pred_group_names.append(pred_group.get_name())

# ---------------------------
# 9. layer control
# ---------------------------
folium.LayerControl(collapsed=True).add_to(map_obj)

# ---------------------------
# 10. sliders and filters
# ---------------------------
map_id = map_obj.get_name()
actual_group_name = marker_group.get_name()

# create a js array for predicted groups using their variable names stored in pred_group_names
pred_groups_js_array = ", ".join([f'window["{name}"]' for name in pred_group_names])

slider_html = f"""
<div id="slider65_container" style="position: fixed; bottom: 160px; left: 10px; z-index:9999; background: white; padding: 5px;">
  <label for="slider65">65+ Minimum (%): </label>
  <input type="range" id="slider65" min="0" max="100" value="0" step="1">
  <span id="value65">0</span>
</div>
<div id="slider85_container" style="position: fixed; bottom: 120px; left: 10px; z-index:9999; background: white; padding: 5px;">
  <label for="slider85">85+ Minimum (%): </label>
  <input type="range" id="slider85" min="0" max="100" value="0" step="1">
  <span id="value85">0</span>
</div>
<div id="pred_filter_container" style="position: fixed; bottom: 80px; left: 10px; z-index:9999; background: white; padding: 5px;">
  <label for="pred_filter">Predicted Filter: </label>
  <select id="pred_filter">
    <option value="all">All</option>
    <option value="increase">Increase Only</option>
    <option value="decrease">Decrease Only</option>
  </select>
</div>
<div id="year_slider_container" style="position: fixed; bottom: 40px; left: 10px; z-index:9999; background: white; padding: 5px;">
  <label for="year_slider">Years Ahead: </label>
  <input type="range" id="year_slider" min="0" max="10" value="0" step="1">
  <span id="year_value">0</span>
</div>
<script>
document.addEventListener("DOMContentLoaded", function() {{
    var slider65 = document.getElementById("slider65");
    var slider85 = document.getElementById("slider85");
    var predFilter = document.getElementById("pred_filter");
    var yearSlider = document.getElementById("year_slider");
    var yearValueDisplay = document.getElementById("year_value");
    var map_instance = window["{map_id}"];
    var actualGroup = window["{actual_group_name}"];
    var predGroups = [ {pred_groups_js_array} ];
    
    // currentGroup references the group whose markers we are updating.
    var currentGroup = actualGroup; // default to actual data (year 0)
    
    function updateMarkers() {{
      var threshold65 = parseFloat(slider65.value);
      var threshold85 = parseFloat(slider85.value);
      var predMode = predFilter.value; // "all", "increase", or "decrease"
      document.getElementById("value65").innerHTML = threshold65;
      document.getElementById("value85").innerHTML = threshold85;
      
      currentGroup.eachLayer(function(marker) {{
          var isPredicted = (marker.options.predicted65 !== undefined);
          if (!isPredicted) {{
              var val65 = marker.options.percent65;
              var val85 = marker.options.percent85;
              var visible = (val65 >= threshold65 && val85 >= threshold85);
          }} else {{
              var val65 = marker.options.predicted65;
              var val85 = marker.options.predicted85;
              var visible = (val65 >= threshold65 && val85 >= threshold85);
              if (predMode === "increase") {{
                  var actual65 = marker.options.actual65;
                  if (!(val65 > actual65)) {{
                      visible = false;
                  }}
              }} else if (predMode === "decrease") {{
                  var actual65 = marker.options.actual65;
                  if (!(val65 < actual65)) {{
                      visible = false;
                  }}
              }}
          }}
          if (visible) {{
              marker.setStyle({{opacity: 1, fillOpacity: 0.8}});
          }} else {{
              marker.setStyle({{opacity: 0, fillOpacity: 0}});
          }}
      }});
    }}
    
    function updateActiveGroup() {{
        var selectedYear = parseInt(yearSlider.value);
        yearValueDisplay.innerHTML = selectedYear;
        // Remove all candidate groups (actual and predicted) from the map.
        if (map_instance.hasLayer(actualGroup)) {{
            map_instance.removeLayer(actualGroup);
        }}
        predGroups.forEach(function(pg) {{
            if (map_instance.hasLayer(pg)) {{
                map_instance.removeLayer(pg);
            }}
        }});
        if (selectedYear === 0) {{
            map_instance.addLayer(actualGroup);
            currentGroup = actualGroup;
        }} else {{
            // For years 1–10, add the corresponding predicted group.
            map_instance.addLayer(predGroups[selectedYear - 1]);
            currentGroup = predGroups[selectedYear - 1];
        }}
        updateMarkers();
    }}
    
    slider65.addEventListener("input", updateMarkers);
    slider65.addEventListener("change", updateMarkers);
    slider85.addEventListener("input", updateMarkers);
    slider85.addEventListener("change", updateMarkers);
    predFilter.addEventListener("change", updateMarkers);
    yearSlider.addEventListener("input", updateActiveGroup);
    yearSlider.addEventListener("change", updateActiveGroup);

    updateActiveGroup(); // Ensure the correct group is selected at startup
    updateMarkers(); // Apply the filtering logic immediately
}});
</script>
"""

map_obj.get_root().html.add_child(Element(slider_html))

# ---------------------------
# 11. save map
# ---------------------------
map_obj.save('map.html')
