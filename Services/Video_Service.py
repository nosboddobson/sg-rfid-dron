import pandas as pd
import cv2
import matplotlib.pyplot as plt
import numpy as np
import json
import os
from datetime import datetime

    
def parse_location(location_code):
    """Extrae fila y sección de un código de ubicación P02FFFCCC"""
    if not location_code or not isinstance(location_code, str):
        return None, None
    
    try:
        if len(location_code) >= 9 and location_code.startswith('P02'):
            # Extraer fila y sección (columna)
            fila = location_code[3:6]  # Ejemplo: "009"
            seccion = location_code[6:9]  # Ejemplo: "001"
        
            row = seccion 
            column = fila.lstrip('0') 
            
            return row, column
    except Exception as e:
        print(f"Error al parsear ubicación '{location_code}': {e}")
    return None, None

def load_route_from_csv(csv_path):
    """Carga el CSV y construye una ruta basada en las ubicaciones"""
    # Cargar el CSV
    df = pd.read_csv(csv_path, sep=';')
    
    # Verificar que exista la columna Ubicacion
    if 'Ubicacion' not in df.columns:
        print("Error: El CSV no contiene la columna 'Ubicacion'")
        return []
    
    unique_locations = df['Ubicacion'].dropna().unique()
    route_points = []
    
    for loc in unique_locations:
        row, section = parse_location(loc)
        if row and section:
            # Convertir a formato "fila-columna" para el bounding box
            route_point = f"{row.zfill(3)}-{section}"
            route_points.append(route_point)
    
    # Eliminar duplicados manteniendo el orden
    route_points = list(dict.fromkeys(route_points))
    
    return route_points

def load_route_from_df(df):

    # Verificar que exista la columna Ubicacion
    if 'Ubicacion' not in df.columns:
        print("Error: El Dataframe no contiene la columna 'Ubicacion'")
        return []
    
    unique_locations = df['Ubicacion'].dropna().unique()
    route_points = []
    
    for loc in unique_locations:
        row, section = parse_location(loc)
        if row and section:
            # Convertir a formato "fila-columna" para el bounding box
            route_point = f"{row.zfill(3)}-{section}"
            route_points.append(route_point)
    
    # Eliminar duplicados manteniendo el orden
    route_points = list(dict.fromkeys(route_points))
    
    return route_points

def create_drone_route_video(json_path, image_path, output_video_path, df_jde):
    """Crea un video simulando un dron que sigue ruta basada en CSV"""
    # Cargar la ruta desde el CSV
    #route = load_route_from_csv(csv_path)
    route=load_route_from_df(df_jde)

    if not route:
        print("No se pudo crear una ruta válida desde el DF")
        return None
    
    print(f"Ruta creada desde df: {route}")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    cell_dict = {}
    for cell in data['bounding_boxes']['grid_cells']:
        key = f"{cell['row']}-{cell['column']}"
        cell_dict[key] = cell['bbox']
    
    # solo ubicaciones que existen en el mapa
    valid_route = [point for point in route if point in cell_dict]
    
    if not valid_route:
        print("Ninguna ubicación del CSV corresponde a las celdas del mapa")
        return None
    
    print(f"Ruta válida: {valid_route}")
    
    img = cv2.imread(image_path)
    height, width, channels = img.shape
    
    # video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 30
    video_out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    # Dibujar base con todos los bounding boxes
    base_img = img.copy()
    for cell in data['bounding_boxes']['grid_cells']:
        bbox = cell['bbox']
        row = cell['row']
        col = cell['column']
        
        # Color según columna
        #if col == "10":
        #    color = (0, 0, 255)
        #else:
        #    color = (50, 205, 50) if int(col) % 2 == 0 else (255, 0, 255)
        
        #cv2.rectangle(base_img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
        
        # Etiqueta pequeña
        #label = f"{row}-{col}"
        #cv2.putText(base_img, label, (bbox[0], bbox[1]-5), 
        #           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
    
    # Convertir a RGB para matplotlib
    base_img_rgb = cv2.cvtColor(base_img, cv2.COLOR_BGR2RGB)
    
    # Procesar centros de ruta
    route_centers = []
    for location in valid_route:
        if location in cell_dict:
            bbox = cell_dict[location]
            center_x = (bbox[0] + bbox[2]) // 2
            center_y = (bbox[1] + bbox[3]) // 2
            route_centers.append((location, (center_x, center_y)))
    
    # Frames iniciales - mostrar mapa completo
    preview_img = base_img_rgb.copy()
    for i in range(len(route_centers) - 1):
        _, current_pos = route_centers[i]
        _, next_pos = route_centers[i + 1]
        cv2.line(preview_img, current_pos, next_pos, (0, 255, 255), 2)
    
    title = f"Ruta de Inventario: {len(valid_route)} ubicaciones"
    cv2.putText(preview_img, title, (width//20, height//15), 
               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
    
    # vista previa
    for _ in range(fps * 3):
        video_out.write(cv2.cvtColor(preview_img, cv2.COLOR_RGB2BGR))
    
    # animación 
    frames_between_points = fps * 2
    drone_size = width // 80
    
    # historial de ruta
    path_history = []
    if route_centers:
        path_history.append(route_centers[0][1])
    
    # animación de cada segmento
    for i in range(len(route_centers) - 1):
        current_location, current_pos = route_centers[i]
        next_location, next_pos = route_centers[i + 1]
        
        print(f"Animando: {current_location} → {next_location}")
        
        # interpolacion de posiciones
        positions = []
        for j in range(frames_between_points):
            t = j / frames_between_points
            x = int(current_pos[0] * (1 - t) + next_pos[0] * t)
            y = int(current_pos[1] * (1 - t) + next_pos[1] * t)
            positions.append((x, y))
        
        # generacion de frames
        for j, pos in enumerate(positions):
            frame = base_img_rgb.copy()
            
            if len(path_history) > 1:
                for k in range(len(path_history) - 1):
                    cv2.line(frame, path_history[k], path_history[k + 1], (0, 100, 255), 2)
            
            cv2.line(frame, current_pos, next_pos, (0, 255, 255), 2)
            
            current_bbox = cell_dict[current_location]
            next_bbox = cell_dict[next_location]
            
            cv2.rectangle(frame, 
                         (current_bbox[0], current_bbox[1]), 
                         (current_bbox[2], current_bbox[3]), 
                         (0, 255, 255), 3)
            cv2.rectangle(frame, 
                         (next_bbox[0], next_bbox[1]), 
                         (next_bbox[2], next_bbox[3]), 
                         (0, 255, 255), 3)
            
            # dron
            color = (0, 165, 255)
            near_endpoint = j < frames_between_points * 0.1 or j > frames_between_points * 0.9
            thickness = 3 if not near_endpoint else 5
            
            # principal
            cv2.circle(frame, pos, drone_size, color, thickness)
            
            # helices   
            line_length = drone_size * 1.3
            cv2.line(frame, 
                    (int(pos[0] - line_length), int(pos[1] - line_length)),
                    (int(pos[0] + line_length), int(pos[1] + line_length)),
                    color, thickness)
            cv2.line(frame, 
                    (int(pos[0] + line_length), int(pos[1] - line_length)),
                    (int(pos[0] - line_length), int(pos[1] + line_length)),
                    color, thickness)
            
            info_text = f"Ruta: {current_location} → {next_location}"
            progress = f"Progreso: {i+1}/{len(route_centers)-1}"
            cv2.putText(frame, info_text, (width//20, height//15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
            cv2.putText(frame, progress, (width//20, height//15 + 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Guardar frame
            video_out.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            
            if j == len(positions) - 1:
                path_history.append(pos)
    
    final_frame = base_img_rgb.copy()
    for i in range(len(path_history) - 1):
        cv2.line(final_frame, path_history[i], path_history[i + 1], (0, 100, 255), 3)
    
    if path_history:
        final_pos = path_history[-1]
        # Dibujar dron final
        cv2.circle(final_frame, final_pos, drone_size, (0, 255, 255), 5)
        line_length = drone_size * 1.2
        cv2.line(final_frame, 
                (int(final_pos[0] - line_length), int(final_pos[1] - line_length)),
                (int(final_pos[0] + line_length), int(final_pos[1] + line_length)),
                (0, 255, 255), 5)
        cv2.line(final_frame, 
                (int(final_pos[0] + line_length), int(final_pos[1] - line_length)),
                (int(final_pos[0] - line_length), int(final_pos[1] + line_length)),
                (0, 255, 255), 5)
    
    cv2.putText(final_frame, "Inventario Completo", (width//20, height//15), 
               cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
    
    for _ in range(fps * 5):
        video_out.write(cv2.cvtColor(final_frame, cv2.COLOR_RGB2BGR))
    
    video_out.release()
    print(f"Video guardado en: {output_video_path}")
    return True


def create_dron_video(df_jde,ID_Vuelo):

     output_video_path_base = 'Video_Vuelos/videos/vuelos/'
     json_path = 'Video_Vuelos/Video_Json/patioMina2.json'
     image_path = 'Video_Vuelos/layout/layout_patio_mina2.png'
     output_video_path = output_video_path_base + str(ID_Vuelo) +'_inventario_vuelo.mp4'

     for path, desc in [(json_path, "JSON de bounding boxes"), 
                        (image_path, "imagen del layout")]:
        if not os.path.exists(path):
            print(f"Error: No se encontró el archivo {desc} en {path}")
            return None

        
        if create_drone_route_video(json_path, image_path, output_video_path, df_jde,ID_Vuelo) is True:
            return output_video_path
        else:
            return None
        
