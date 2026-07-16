import folium  
print("Version folium:", folium.__version__)  
m = folium.Map(location=[11.4, -69.6], cdn_resources="inline")  
html = m.get_root().render()  
print("Tamano HTML:", len(html))  
print("Contiene L.map(:", "L.map(" in html)  
print("Contiene cdn.jsdelivr:", "cdn.jsdelivr" in html) 
