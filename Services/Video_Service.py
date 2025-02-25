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
    #fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fourcc = cv2.VideoWriter_fourcc(*'X264')
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

     output_video_path_base = 'Webserver/videos/'
     json_path = 'Video_Vuelos/Video_Json/patioMina2.json'
     image_path = 'Video_Vuelos/layout/layout_patio_mina2.png'
     output_video_path = output_video_path_base + str(ID_Vuelo) +'_inventario_vuelo.mp4'

     for path, desc in [(json_path, "JSON de bounding boxes"), 
                        (image_path, "imagen del layout")]:
        if not os.path.exists(path):
            print(f"Error: No se encontró el archivo {desc} en {path}")
            return None

        
        if create_drone_route_video(json_path, image_path, output_video_path, df_jde) is True:
            return output_video_path
        else:
            return None
        
def create_dron_video_3d(df_jde,ID_Vuelo):

    output_video_path_base = 'Webserver/videos/'
    json_path = 'Video_Vuelos/Video_Json/bounding-boxes_pm2_3d.json'
    image_path = 'Video_Vuelos/layout/layout_patio_mina2_3d.png'
    output_video_path = output_video_path_base + str(ID_Vuelo) +'_inventario_vuelo.mp4'

    route=load_route_from_df(df_jde)

    if not route:
        print("No se pudo crear una ruta válida desde el DF")
        return None

    for path, desc in [(json_path, "JSON de bounding boxes"), 
                        (image_path, "imagen del layout")]:
        if not os.path.exists(path):
            print(f"Error: No se encontró el archivo {desc} en {path}")
            return None

        
        if create_drone_flight_video_3d(json_path, image_path, output_video_path, route) is True:
            return output_video_path
        else:
            return None
        
def create_dron_video_3d_test(ID_Vuelo):

    output_video_path_base = 'Webserver/videos/'
    json_path = 'Video_Vuelos/Video_Json/bounding-boxes_pm2_3d.json'
    image_path = 'Video_Vuelos/layout/layout_patio_mina2_3d.png'
    output_video_path = output_video_path_base + str(ID_Vuelo) +'_inventario_vuelo.mp4'

    # OPCIÓN 1: Usando las coordenadas fila-columna
    route_by_position = [
        "004-1",  # Inicio en el polígono 1
        "004-2",  # Ir al polígono 2
        "004-3",  # Ir al polígono 3
        "003-4",  # Ir al polígono 13
        "003-5",  # Ir al polígono 14
        "003-6",  # Ir al polígono 15
        "002-7",  # Ir al polígono 25
        "002-8",  # Ir al polígono 26
        "001-9",  # Ir al polígono 36
        "001-1",  # Ir al polígono 28
        "004-1"   # Volver al polígono 1
    ]
    
    # OPCIÓN 2: Usando directamente los IDs de los polígonos
    route_by_ids = [
        "poligono_36",  # Inicio en 36
        "poligono_27",  # Ir a 27
        "poligono_18",  # Ir a 18
        "poligono_9",   # Ir a 9
        "poligono_8",   # Ir a 8
        "poligono_17",  # Ir a 17
        "poligono_26",  # Ir a 26
        "poligono_35",  # Ir a 35
        "poligono_35",  # Permanecer en 35 (repetido en la ruta)
        "poligono_26",  # Volver a 26
        "poligono_17",  # Volver a 17
        "poligono_8",   # Volver a 8
        "poligono_7",   # Ir a 7
        "poligono_16",  # Ir a 16
        "poligono_25",  # Ir a 25
        "poligono_34"   # Finalizar en 34
    ]
    
    # Selecciona la ruta que prefieras usar
    route = route_by_ids  # o route_by_position

    if not route:
        print("No se pudo crear una ruta válida desde el DF")
        return None

    for path, desc in [(json_path, "JSON de bounding boxes"), 
                        (image_path, "imagen del layout")]:
        if not os.path.exists(path):
            print(f"Error: No se encontró el archivo {desc} en {path}")
            return None

        
        if create_drone_flight_video_3d(json_path, image_path, output_video_path, route) is True:
            return output_video_path
        else:
            return None


def create_drone_flight_video_3d(json_path, image_path, output_video_path, route):
    # Cargar el JSON con los bounding boxes
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Crear un diccionario para acceder fácilmente a las celdas por ID del polígono y por fila-columna
    cell_dict_by_position = {}
    cell_dict_by_id = {}
    
    for cell in data['bounding_boxes']['grid_cells']:
        # Guardar por posición fila-columna
        key_position = f"{cell['row']}-{cell['column']}"
        cell_dict_by_position[key_position] = cell['bbox']
        
        # Guardar por ID de polígono
        key_id = cell['id']
        cell_dict_by_id[key_id] = cell['bbox']
    
    # Cargar la imagen
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: No se pudo cargar la imagen desde {image_path}")
        return
    height, width, channels = img.shape
    # video
    #fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fourcc = cv2.VideoWriter_fourcc(*'X264')
    fps = 30
    video_out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    # Obtener dimensiones de la imagen
    
    print(f"Dimensiones de la imagen: {width}x{height}")
    

    if not video_out.isOpened():
        print("Error crítico: No se puede crear el archivo de video con ningún códec.")
        return None
    
    print(f"Configuración de video: {width}x{height}, {fps} fps, códec: {chr(fourcc & 0xFF) + chr((fourcc >> 8) & 0xFF) + chr((fourcc >> 16) & 0xFF) + chr((fourcc >> 24) & 0xFF)}")
    
    # Dibujar todos los bounding boxes (como referencia)
    def draw_all_boxes(image):
        img_copy = image.copy()
        #for cell in data['bounding_boxes']['grid_cells']:
        #    bbox = cell['bbox']
        #    cell_id = cell['id']
            
            # Extraer el número del polígono para determinar el color
            #poligono_num = 0
            #if cell_id.startswith("poligono_"):
            #    poligono_num = int(cell_id.split("_")[1])
            #else:
            #    num_str = ''.join(filter(str.isdigit, cell_id))
            #    poligono_num = int(num_str) if num_str else 0
            
            # Alternar color según número de polígono
            #color = (50, 205, 50) if poligono_num % 2 == 0 else (255, 0, 255)
            
            # Dibujar rectángulo con borde más fino
            #cv2.rectangle(img_copy, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            
            #etiqueta con el número del polígono
            #font_scale = 0.7
            #label = str(poligono_num)
            #cv2.putText(img_copy, label, (bbox[0], bbox[1]-5), 
            #            cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1)
        
        return img_copy
    
    def get_box_center(box_key):
        
        if box_key in cell_dict_by_position:
            bbox = cell_dict_by_position[box_key]
            center_x = (bbox[0] + bbox[2]) // 2
            center_y = (bbox[1] + bbox[3]) // 2
            return (center_x, center_y)
        
        elif box_key in cell_dict_by_id:
            bbox = cell_dict_by_id[box_key]
            center_x = (bbox[0] + bbox[2]) // 2
            center_y = (bbox[1] + bbox[3]) // 2
            return (center_x, center_y)
        
        else:
            print(f"Advertencia: La celda {box_key} no existe en el JSON")
            return None
    
    def get_polygon_by_position(position_key):
        for cell in data['bounding_boxes']['grid_cells']:
            if f"{cell['row']}-{cell['column']}" == position_key:
                return cell['id']
        return None
    
    def draw_drone(image, position, size=50, highlight=False):
        img_copy = image.copy()
        
        #círculo para el dron
        color = (0, 165, 255) if not highlight else (0, 255, 255)  # Naranja o amarillo
        thickness = 3 if not highlight else 5
        
        # circulo principal
        cv2.circle(img_copy, position, size, color, thickness)
        
        # helices (líneas cruzadas)
        line_length = size * 1.2
        cv2.line(img_copy, 
                 (int(position[0] - line_length), int(position[1] - line_length)),
                 (int(position[0] + line_length), int(position[1] + line_length)),
                 color, thickness)
        cv2.line(img_copy, 
                 (int(position[0] + line_length), int(position[1] - line_length)),
                 (int(position[0] - line_length), int(position[1] + line_length)),
                 color, thickness)
        
        # punto medio
        cv2.circle(img_copy, position, 5, (0, 0, 255), -1)
        
        return img_copy
    
    #nterpolar posiciones entre dos puntos
    def interpolate_positions(start_pos, end_pos, num_frames):
        positions = []
        for i in range(num_frames):
            t = i / num_frames
            x = int(start_pos[0] * (1 - t) + end_pos[0] * t)
            y = int(start_pos[1] * (1 - t) + end_pos[1] * t)
            positions.append((x, y))
        return positions
    
    print("Generando video de la ruta circular del dron...")
    route_centers = []
    for location in route:
        center = get_box_center(location)
        if center:
            polygon_id = get_polygon_by_position(location) if "-" in location else location
            route_centers.append((location, center, polygon_id))

    base_img = draw_all_boxes(img)
    
    # dibujo de toda la ruta completa para visualizarla
    preview_img = base_img.copy()
    for i in range(len(route_centers) - 1):
        _, current_pos, _ = route_centers[i]
        _, next_pos, _ = route_centers[i + 1]
        cv2.line(preview_img, current_pos, next_pos, (0, 255, 255), 2)
    
    # vista previa de la ruta
    for _ in range(fps * 3):  # 3 segundos
        video_out.write(preview_img)
    
    # animación del dron
    frames_between_points = fps * 2  # 2 segundos por movimiento
    drone_size = width // 80  # Tamaño relativo al ancho de la imagen

    path_history = []
    if len(route_centers) > 0:
        path_history.append(route_centers[0][1])
    
    for i in range(len(route_centers) - 1):
        current_location, current_pos, current_polygon = route_centers[i]
        next_location, next_pos, next_polygon = route_centers[i + 1]
        
        print(f"Animando movimiento: {current_location} → {next_location}")
        
        # interpoliación de posiciones para movimiento suave
        positions = interpolate_positions(current_pos, next_pos, frames_between_points)
        
        for j, pos in enumerate(positions):
         
            frame = base_img.copy()
            
            # historia de la ruta recorrida
            if len(path_history) > 1:
                for k in range(len(path_history) - 1):
                    cv2.line(frame, path_history[k], path_history[k + 1], (0, 100, 255), 2)
            
            # línea al siguiente punto
            cv2.line(frame, current_pos, next_pos, (0, 255, 255), 2)
            
            # Obtener los bounding boxes de la posición actual y la siguiente
            if "-" in current_location:
                current_bbox = cell_dict_by_position[current_location]
            else:
                current_bbox = cell_dict_by_id[current_location]
                
            if "-" in next_location:
                next_bbox = cell_dict_by_position[next_location]
            else:
                next_bbox = cell_dict_by_id[next_location]
            
            # celda actual
            highlight_color = (0, 255, 255)  # Amarillo
            cv2.rectangle(frame, 
                         (current_bbox[0], current_bbox[1]), 
                         (current_bbox[2], current_bbox[3]), 
                         highlight_color, 3)
            cv2.rectangle(frame, 
                         (next_bbox[0], next_bbox[1]), 
                         (next_bbox[2], next_bbox[3]), 
                         highlight_color, 3)
            
            # se destaca el dron cuando esté cerca del inicio o fin
            near_endpoint = j < frames_between_points * 0.1 or j > frames_between_points * 0.9
            frame = draw_drone(frame, pos, drone_size, highlight=near_endpoint)
            
            text = f"Ruta: "
            if current_polygon:
                text += f"Polígono {current_polygon.split('_')[1]} → "
            else:
                text += f"{current_location} → "
                
            if next_polygon:
                text += f"Polígono {next_polygon.split('_')[1]}"
            else:
                text += f"{next_location}"
                
            progress = f"Progreso: {i+1}/{len(route_centers)-1}"
            cv2.putText(frame, text, (width//20, height//15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
            cv2.putText(frame, progress, (width//20, height//15 + 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            video_out.write(frame)
            
            # posición al historial si es el último frame
            if j == len(positions) - 1:
                path_history.append(pos)
    
    # frame finales - mantener el último punto por unos segundos
    final_frame = base_img.copy()
    
    # la ruta completa
    for i in range(len(path_history) - 1):
        cv2.line(final_frame, path_history[i], path_history[i + 1], (0, 100, 255), 3)
    
    # dron en posición final
    final_frame = draw_drone(final_frame, path_history[-1], drone_size, highlight=True)
    
    # texto de finalización
    cv2.putText(final_frame, "Ruta Completada", (width//20, height//15), 
               cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
    
    for _ in range(fps * 5):  # 5 segundos en posición final
        video_out.write(final_frame)
    
    video_out.release()
    print(f"Video guardado en: {output_video_path}")
    
    if os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
        print(f"archivo de video se creó correctamente ({os.path.getsize(output_video_path)/1024/1024:.2f} MB)")
        return True
    else:
        print(f"Error: archivo de video no se creó o está vacío.")
        return None

if __name__ == "__main__":
     create_dron_video_3d_test(42)
