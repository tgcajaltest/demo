"""Funciones para demo de aplicativo de asignación de medios."""
import numpy as np
import pandas as pd
import geopandas as gpd 
import matplotlib.pyplot as plt 

import folium 
import geopandas as gpd 
import shapely
from shapely import Polygon
import streamlit as st

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

# Función para asignar recursos a los cuadrantes y actualizar 'Oferta_total'-------------------------------------------------------------------
# Función para asignar recursos a los cuadrantes y actualizar 'Oferta_total'
def asignar_recursos(df_necesidades, df_recursos, asignacionC):
    # Iterar sobre cada cuadrante
    for index, row in df_necesidades.iterrows():
        cuadrante = index
        necesidad = row['Necesidad']
        print(f"\nAsignando recursos para Cuadrante {cuadrante} con necesidad {necesidad}")
        
        # Filtrar recursos disponibles donde Medio es 'RPT'
        recursos_disponibles = df_recursos[(df_recursos[asignacionC] == 0) & (df_recursos['Medio'] == 'RPT')]

        
        # Asignar recursos hasta cubrir la necesidad
        while necesidad > 0 and not recursos_disponibles.empty:
            # Tomar un recurso disponible aleatoriamente
            recurso_index = recursos_disponibles.sample().index[0]
            oferta_unitaria = recursos_disponibles.loc[recurso_index, 'Oferta Unitaria']
            
            # Asignar el recurso al cuadrante
            df_recursos.at[recurso_index, asignacionC] = cuadrante
            necesidad -= oferta_unitaria
            print(f"Asignado recurso {recurso_index} con oferta unitaria {oferta_unitaria}")
            
            # Actualizar 'Oferta_total' en el DataFrame de necesidades
            df_necesidades.at[index, 'Oferta_Total'] += oferta_unitaria
            
            # Actualizar recursos disponibles
            recursos_disponibles = df_recursos[(df_recursos[asignacionC] == 0) & (df_recursos['Medio'] == 'RPT')]

        
        if necesidad > 0:
            print(f"No se pudo cubrir la necesidad completa para Cuadrante {cuadrante}. Necesidad restante: {necesidad}")
        else:
            print(f"Necesidad cubierta para Cuadrante {cuadrante}")

    
    df_necesidades['Diferencia'] = df_necesidades['Oferta_Total'] + df_necesidades['Cuarteles'] - df_necesidades['Necesidad']
    recursos_disponibles = df_recursos[df_recursos[asignacionC] == 0]

    df_necesidades['Diferencia'] = df_necesidades['Oferta_Total'] + df_necesidades['Cuarteles'] - df_necesidades['Necesidad']
    df_necesidades = df_necesidades.sort_values(by='Cuadrante')
            
    return df_recursos, df_necesidades
#--///////---//----//----///----//-----//////---//-----///////----///----//------
#--//--------//----//----////---//---//---------//---//------//---////---//------
#--////------//----//----//-//--//--//----------//---//------//---//-//--//-------
#--//--------//----//----//--//-//---//---------//----//----//----//--//-//------
#--//--------///////-----//---////----//////----//-----/////------//---////----

# Función para transformar polígonos
def transform_polygon(shapely_polygon, name):
    """
    Función para convertir polígono shapely en polígono folium.

    Parámetros:
    - shapely_polygon: Polígono shapely.
    - color: Color de línea (default: 'blue').
    - weight: Grosor de línea (default: 2).
    - fill_color: Color de relleno de polígono (default: 'blue').
    - fill_opacity: Opacidad de color de relleno (default: 0.4).

    Output:
    - Objeto polígono folium.
    """
    # Extraer coordenadas
    coordinates = shapely_polygon.exterior.coords.xy

    # Generar puntos 
    latitudes = list(coordinates[1])
    longitudes = list(coordinates[0])
    points = list(zip(latitudes, longitudes))

    # Definir color
    color="deepskyblue"
    fill_color="deepskyblue"

    # Crear polígono folium
    folium_polygon = folium.vector_layers.Polygon(
        locations=points,
        color=color,
        weight=2,
        fill_color=fill_color,
        fill_opacity=0.2,
        tooltip=name
    )

    return folium_polygon


# Función para etiquetas de diferencia
def label_diferencia(cuadrante, df, gdf):
    #df = df.rename(columns={"Id_Cuadrante":"Cuadrante"})
    if type(cuadrante) == str:
        cuadrante_name = cuadrante 
        cuad = cuadrante[-1]
        print(cuadrante_name)
        print(cuad)
    
    elif type(cuadrante) == int:
        cuadrante_name = "SSC-12.0"+str(cuadrante)
        cuad = cuadrante 
        print(cuadrante_name)
        print(cuad)
    
    else:
        print("Revisar formato de cuadrante")

    # Definir polígono
    poligono = gdf[gdf["CUADRANTE_"]==cuadrante_name]["geometry"].values[0]
    center_lat = poligono.centroid.y.mean()
    center_lon = poligono.centroid.x.mean()

    # Definir diferencia
    diferencia = df[df["Id_Cuadrante"]==int(cuad)]["Diferencia"].values[0]

    # Definir color según diferencia
    if diferencia>=0:
        color="green"
    elif diferencia<0:
        color="red"

    # Crear etiqueta
    div_icon = folium.DivIcon(html="""
    <div style="font-family: sans-serif; color: white; background-color:"""+str(color)+"""; padding: 2px 10px; border-radius: 3px; width: 50px; text-align: center;">
        <b>"""+str(round(diferencia,2))+"""</b>
    </div>
    """)

    # Crear objeto marker
    label = folium.Marker(
        location=[center_lat, center_lon],
        icon=div_icon
    ) 

    return label  


from shapely import Point

def get_random_point_near_center(polygon: Polygon, std_dev_factor=0.2):
    centroid = polygon.centroid
    centroid_x, centroid_y = centroid.x, centroid.y
    min_x, min_y, max_x, max_y = polygon.bounds
    
    # Calculate standard deviation based on the polygon size and the factor provided
    std_dev_x = (max_x - min_x) * std_dev_factor
    std_dev_y = (max_y - min_y) * std_dev_factor
    
    while True:
        random_x = np.random.normal(centroid_x, std_dev_x)
        random_y = np.random.normal(centroid_y, std_dev_y)
        random_point = Point(random_x, random_y)
        if polygon.contains(random_point):
            return [random_point.y, random_point.x]

# Coordenadas predefinidas para marcadores de medios en cuadrantes        
predefined_coords = {
    "SSC-12.01": [
        (13.711347, -89.245041), (13.706200, -89.243542), (13.709451, -89.238279),
        (13.704066, -89.229599), (13.704913, -89.238732)
    ],
    "SSC-12.02": [
        (13.699606, -89.244572), (13.696846, -89.242720), (13.698806, -89.234116),
        (13.689046, -89.240456), (13.685677, -89.242013)
    ],
    "SSC-12.03": [
        (13.685677, -89.242013), (13.697569, -89.219173), (13.685726, -89.232846),
        (13.687617, -89.225779), (13.687219, -89.220658)
    ],
    "SSC-12.04": [
        (13.725679, -89.234178), (13.723589, -89.230900), (13.716674, -89.242525),
        (13.715828, -89.237916), (13.714186, -89.233000)
    ],
    "SSC-12.05": [
        (13.714917, -89.228318), (13.712130, -89.221146), (13.710296, -89.226053),
        (13.724232, -89.226808), (13.721665, -89.219862)
    ],
    "SSC-12.06": [
        (13.719245, -89.212841), (13.720272, -89.207782), (13.711397, -89.216087),
        (13.706115, -89.219485), (13.708023, -89.215181)
    ],
    "SSC-12.07": [
        (13.724232, -89.248930), (13.720345, -89.254064), (13.714184, -89.251422),
        (13.718291, -89.251271), (13.708169, -89.251195)
    ]
}


def get_predefined_point(polygon_id, index):
    # Coordenadas pre definidas en polígonos
    coords = predefined_coords.get(polygon_id, [])
    if index < len(coords):
        return coords[index]
    else:
        return None  # En caso de no haber suficientes puntos
    
def create_popup_content(id_conjunto, turno, conjuntos):
    rows = conjuntos[(conjuntos['Id_Conjunto'] == int(id_conjunto))&(conjuntos["Turno"]==int(turno))]
    if rows.empty:
        return "No data available"
    
    conjunto = rows.iloc[0]['Id_Conjunto']
    grupo = rows.iloc[0]['Grupo']
    personal_data = ", ".join(f"{row['Rango']} ({row['Tipo']})" for idx, row in rows.iterrows())
    popup_content = (f"Personal: {personal_data}<br>"
                     f"Número de grupo: {grupo}<br>"
                     f"Número de conjunto: {conjunto}")
    return popup_content


#conjuntos = pd.read_excel("conjuntos2.xlsx")

# Función para agregar medios asignados
def viz_medios(conjuntos, df, id_medio, predefined_coords, polygon_counter, id_conjunto, turno):
    id_conjunto = int(id_conjunto)

    tipo = df[df["Id_Medio"] == id_medio]["Medio"].values[0]
    print("Tipo (str): "+str(tipo))
    print("Id medio (int): "+str(id_medio))
    print("Id conjunto (int): "+str(id_conjunto))
    print("Turno: "+str(turno))
    cuadrante = df[df["Id_Medio"] == id_medio]["Asignacion_Cuadrante_T"+str(turno)].values[0]
    cuadrante_name = "SSC-12.0"+str(cuadrante)

    if tipo == "RPT":
        icon = "car"
        color = "darkblue"
    elif tipo == "MTT":
        icon = "motorcycle"
        color = "blue"
    
    # Agregar un contador de cantidad de marcadores por cuadrante
    polygon_id = cuadrante
    #print("polygon_id: "+str(polygon_id)+", type: "+str(type(polygon_id)))

    coord = get_predefined_point(cuadrante_name, polygon_counter[cuadrante_name])
    if coord:
        polygon_counter[cuadrante_name] += 1
        popup_content = create_popup_content(id_conjunto, turno, conjuntos)
        marcador = folium.Marker(
            location=coord, 
            draggable=True,
            popup=popup_content,
            icon=folium.Icon(icon=icon, color=color, prefix='fa')
        )
        return marcador
    else:
        return None  # En caso de coordenadas no válidas
    
def create_marker(df, id_conjunto:int, col):
    """Función para agregar marcadores de patrullas al mapa.
    Parámetros:
    - df (DataFrame): Con información de conjuntos y medios
    - id_conjunto (int): Número de conjunto a visualizar
    - coords: Coordenadas para mapear."""

    # Filtrar
    df = df[df["Id_Conjunto"]==id_conjunto].dropna().reset_index(drop=True)
    df = df[df[col]!=0]

    if len(df) == 0:
        pass
    else:
        print("Miembros en el conjunto: "+str(len(df)))

        # Obtener datos del medio asignado al conjunto
        print("Asignaciones :"+str(len(df[col])))
        cuadrante = df[col].astype(int)[0]
        print("Número de cuadrante: "+str(cuadrante))
        #id_medio = list(df["Id_Medio"])[0]
        tipo_medio = list(df["Medio_x"])[0]
        placa = list(df["Placa"])[0]

        # Definir polígono de cuadrante
        cuadrante_name = "SSC-12.0"+str(cuadrante)
        print("Nombre de cuadrante: "+cuadrante_name)
        poligono = capa[capa["CUADRANTE_"]==cuadrante_name]["geometry"].values[0]

        # Punto al azar dentro de polígono
        coords = get_random_point_near_center(poligono)

        # Definir título popup con estos datos
        html_title = "<h4><b>Conjunto "+str(id_conjunto)+"</b><br><b>Vehículo: "+str(tipo_medio)+" "+str(placa)+"</b></h4>"

        # Dataframe con datos de conjunto a HTML para popup
        html_table = df[["ONI","Rango","Tipo"]].to_html(index=False, classes="table table-striped table-hover table-condensed table-responsive")
        
        # Concatenar título con tabla
        html = html_title + html_table

        # Generar popup con html
        popup = folium.Popup(html, max_width=450)

        # Crear marcador
        marker = folium.Marker(location= coords,
                            popup=popup,
                            draggable=True,
                            icon=folium.Icon(icon="car", color="darkblue", prefix='fa'))
        
        return marker
