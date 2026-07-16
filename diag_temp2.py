import folium 
m = folium.Map(location=[11.4, -69.6], cdn_resources="inline") 
html = m.get_root().render() 
f = open("diag_output.html", "w", encoding="utf-8") 
f.write(html) 
f.close() 
print("Archivo generado: diag_output.html") 
