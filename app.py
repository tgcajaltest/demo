import streamlit as st 
#from streamlit_folium import st_folium
import streamlit.components.v1 as components
import numpy as np
import pandas as pd 
import geopandas as gpd
import folium
import random
from shapely.geometry import Point, Polygon
import funciones as f

st.set_page_config(page_title="Demo", page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

df1 = pd.read_csv("1.csv")
df1 = df1.loc[:,~df1.columns.str.contains("^Unnamed")]
df2 = pd.read_csv("2.csv")
df2 = df2.loc[:,~df2.columns.str.contains("^Unnamed")]
df3 = pd.read_csv("3.csv")
df3 = df3.loc[:,~df3.columns.str.contains("^Unnamed")]

# Capa delegación poniente
capa = gpd.read_file("poniente.json")

# Definir coordenadas centrales
center_lat = capa.geometry.centroid.y.mean()
center_lon = capa.geometry.centroid.x.mean()

# Mapa base
mapa = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=14,
)

# Agregar capa cuadrantes, la constante en todos los mapas a ser renderizados
for x in range(0,len(capa)):
    f.transform_polygon(capa["geometry"].iloc[x],capa["CUADRANTE_"].iloc[x]).add_to(mapa)

# Agregar diferencia
for x in list(capa["CUADRANTE_"].unique()):
    f.label_diferencia(x,df1,capa).add_to(mapa)

joined = df3.merge(df2, left_on="Placa", right_on="Placa", how="left")

df = joined[["Id_agente","ONI","Rango","Tipo","Id_Conjunto","Id_Medio","Medio_x","Medio_y","Turno","Grupo","Placa","Asignacion_Cuadrante_T1","Asignacion_Cuadrante_T2","Asignacion_Cuadrante_T3","Asignacion_Cuadrante_T4"]]

turno = st.selectbox("Escoger turno: ",[1,2,3,4])

if st.button("Calcular", type="primary") != True:
    print("Escoger turno y calcular")
else:
    t = df[df["Turno"]==turno]
    col = "Asignacion_Cuadrante_T"+str(turno)

    conjuntos = list(t["Id_Conjunto"].unique())

    for conjunto in conjuntos:
        print("Conjunto: "+str(conjunto))
        try:
            marker = f.create_marker(t, conjunto,col)
            marker.add_to(mapa)

        except AttributeError:
            pass

    # Convertir mapa a HTML
    map_html = mapa._repr_html_()

    # Mostrar mapa
    components.html(map_html, width=1200, height=750)
    
    # Agregar opción de descarga
    st.write("Descargas")
    st.download_button("Mapa (html)", data=map_html)
    st.download_button("Conjuntos asignados (csv)", data="3.csv")
