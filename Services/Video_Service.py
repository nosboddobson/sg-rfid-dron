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
            route_point = f"{row.zfill(3)}-{int(int(section)-1)}"
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
            route_point = f"{row.zfill(3)}-{int(int(section)-1)}"
            route_points.append(route_point)
    
    # Eliminar duplicados manteniendo el orden
    route_points = list(dict.fromkeys(route_points))
    
    return route_points


        

def create_dron_video_3d(df_jde,ID_Vuelo):

    output_video_path_base = 'Webserver/videos/'
    json_path = 'Video_Vuelos/Video_Json/PM2_bounding-boxes_3d_20250226.json'
    image_path = 'Video_Vuelos/layout/PM2_3d_20250226.jpg'
    output_video_path = output_video_path_base + str(ID_Vuelo) +'_inventario_vuelo.mp4'
    drone_img_path = 'Video_Vuelos/dji_matrice_350_transparent.png'  # Ruta a la imagen del dron con fondo transparente

    route=load_route_from_df(df_jde)
    #route=df_jde
    
    if not route:
        print("No se pudo crear una ruta válida desde el DF")
        return None

    for path, desc in [(json_path, "JSON de bounding boxes"), 
                        (image_path, "imagen del layout")]:
        if not os.path.exists(path):
            print(f"Error: No se encontró el archivo {desc} en {path}")
            return None

        if create_drone_flight_video(json_path,image_path,drone_img_path,output_video_path,route) is True:

            return output_video_path
        else:
            return None
        
def create_dron_video_3d_test(ID_Vuelo):

    output_video_path_base = 'Webserver/videos/'
    json_path = 'Video_Vuelos/Video_Json/PM2_bounding-boxes_3d_20250226.json'
    image_path = 'Video_Vuelos/layout/PM2_3d_20250226.jpg'
    output_video_path = output_video_path_base + str(ID_Vuelo) +'_inventario_vuelo.mp4'
    drone_img_path = 'Video_Vuelos/dji_matrice_350_transparent.png'  # Ruta a la imagen del dron con fondo transparente

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

        if create_drone_flight_video(json_path,image_path,drone_img_path,output_video_path,route) is True:
        
        #if create_drone_flight_video_3d(json_path, image_path, output_video_path, route) is True:
            return output_video_path
        else:
            return None


def create_drone_flight_video(json_path, image_path, drone_img_path, output_video_path, route):
    # Cargar el JSON con los bounding boxes
    print('create_drone_flight_video iniciado')
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    cell_dict_by_position = {}
    cell_dict_by_id = {}
    
    for cell in data['bounding_boxes']['grid_cells']:

        key_position = f"{cell['row']}-{cell['column']}"
        cell_dict_by_position[key_position] = cell['bbox']

        key_id = cell['id']
        cell_dict_by_id[key_id] = cell['bbox']
    
    # Cargar la imagen
    print('Cargando Imagen base para Video')
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: No se pudo cargar la imagen desde {image_path}")
        return None
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
    

    def draw_all_boxes(image):
        img_copy = image.copy()
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
    
    def overlay_transparent(background, foreground, x_offset, y_offset):
        """
        Coloca una imagen con transparencia (BGRA) sobre otra imagen.
        
        Args:
            background: Imagen de fondo (BGR o BGRA)
            foreground: Imagen a sobreponer con transparencia (BGRA)
            x_offset: Posición X donde colocar la esquina superior izquierda
            y_offset: Posición Y donde colocar la esquina superior izquierda
        """
        bg_h, bg_w = background.shape[:2]
        fg_h, fg_w = foreground.shape[:2]
        
        x1 = max(0, x_offset)
        y1 = max(0, y_offset)
        x2 = min(bg_w, x_offset + fg_w)
        y2 = min(bg_h, y_offset + fg_h)
        
        fg_x1 = max(0, -x_offset)
        fg_y1 = max(0, -y_offset)
        fg_x2 = fg_x1 + (x2 - x1)
        fg_y2 = fg_y1 + (y2 - y1)
        
        if x2 <= x1 or y2 <= y1 or fg_x2 <= fg_x1 or fg_y2 <= fg_y1:
            return
    
        foreground_region = foreground[fg_y1:fg_y2, fg_x1:fg_x2]

        if background.shape[2] == 3:
            background_region = background[y1:y2, x1:x2]
            background_region_alpha = np.ones((y2-y1, x2-x1), dtype=np.uint8) * 255
            background_region_with_alpha = cv2.merge([
                background_region[:,:,0],
                background_region[:,:,1],
                background_region[:,:,2],
                background_region_alpha
            ])
        else:
            background_region_with_alpha = background[y1:y2, x1:x2]
        

        alpha = foreground_region[:, :, 3] / 255.0
        alpha = alpha[:, :, np.newaxis]
        
        # Invertir el canal alfa para el fondo
        inv_alpha = 1.0 - alpha
        
  
        result = alpha * foreground_region[:, :, :3] + inv_alpha * background_region_with_alpha[:, :, :3]

        if background.shape[2] == 3:
            background[y1:y2, x1:x2] = result
        else:
            result_with_alpha = cv2.merge([
                result[:,:,0],
                result[:,:,1],
                result[:,:,2],
                background_region_with_alpha[:,:,3]
            ])
            background[y1:y2, x1:x2] = result_with_alpha
    
    def calculate_dynamic_drone_size(current_bbox, next_bbox, progress, base_size, min_factor=0.6, max_factor=1.5):
        """
        Calcula un tamaño dinámico para el dron basado en el tamaño de la celda actual y siguiente.
        
        Args:
            current_bbox: Bounding box de la celda actual [x1, y1, x2, y2]
            next_bbox: Bounding box de la celda siguiente [x1, y1, x2, y2]
            progress: Valor entre 0 y 1 que indica la progresión entre los dos puntos
            base_size: Tamaño base de referencia
            min_factor: Factor mínimo de escala
            max_factor: Factor máximo de escala
            
        Returns:
            Tamaño dinámico del dron en píxeles
        """

        current_width = current_bbox[2] - current_bbox[0]
        current_height = current_bbox[3] - current_bbox[1]
        next_width = next_bbox[2] - next_bbox[0]
        next_height = next_bbox[3] - next_bbox[1]
        
        # Interpolar entre los tamaños
        width_at_progress = current_width * (1 - progress) + next_width * progress
        height_at_progress = current_height * (1 - progress) + next_height * progress
        
        cell_size = min(width_at_progress, height_at_progress)
        
        # Calcular el tamaño como un porcentaje del tamaño de la celda
        size_relative_to_cell = cell_size / 3.5 
        
        # Aplicar límites basados en el tamaño base
        min_size = base_size * min_factor
        max_size = base_size * max_factor
        
        # Limitar el tamaño final
        final_size = max(min_size, min(size_relative_to_cell, max_size))
        
        return int(final_size)
    
    def draw_drone_with_image(image, position, drone_img_path, size=100, highlight=False):
        """
        Dibuja la imagen del dron en la posición especificada.
        
        Args:
            image: Imagen base donde se dibujará el dron
            position: Tupla (x, y) con la posición central donde colocar el dron
            drone_img_path: Ruta a la imagen PNG del dron con fondo transparente
            size: Tamaño del dron (ancho en píxeles)
            highlight: Si True, añade un efecto de resaltado al dron
        
        Returns:
            Imagen con el dron dibujado
        """
        img_copy = image.copy()
        
        # Cargar la imagen del dron con transparencia
        drone_img = cv2.imread(drone_img_path, cv2.IMREAD_UNCHANGED)
        
        if drone_img is None:
            print(f"Error: No se pudo cargar la imagen del dron desde {drone_img_path}")
            # Fallback al método anterior de dibujo (si fuera necesario)
            return draw_drone_fallback(img_copy, position, size//2, highlight)
        

        if drone_img.shape[2] < 4:
            print("Advertencia: La imagen del dron no tiene canal de transparencia, convirtiéndola...")
            drone_img = cv2.cvtColor(drone_img, cv2.COLOR_BGR2BGRA)
        
        # Redimensionar el dron al tamaño deseado
        aspect_ratio = drone_img.shape[1] / drone_img.shape[0] 
        new_width = size
        new_height = int(new_width / aspect_ratio)
        drone_img = cv2.resize(drone_img, (new_width, new_height))
        

        x_offset = position[0] - new_width // 2
        y_offset = position[1] - new_height // 2
        

        if highlight:

            alpha_channel = drone_img[:, :, 3]
            kernel = np.ones((5, 5), np.uint8)
            dilated_mask = cv2.dilate(alpha_channel, kernel, iterations=2)
            
            # Crear una versión del dron con borde amarillo
            glow_img = drone_img.copy()

            glow_mask = cv2.subtract(dilated_mask, alpha_channel)
            glow_img[glow_mask > 0, 0] = 0    # B
            glow_img[glow_mask > 0, 1] = 255  # G
            glow_img[glow_mask > 0, 2] = 255  # R
            glow_img[glow_mask > 0, 3] = 200  # A 
            
            # Sobreponemos primero el resplandor
            overlay_transparent(img_copy, glow_img, x_offset, y_offset)
        
        # Sobreponer la imagen del dron en la imagen base
        overlay_transparent(img_copy, drone_img, x_offset, y_offset)
        
        return img_copy
    
  
    def draw_drone_fallback(image, position, size=50, highlight=False):
        img_copy = image.copy()
        
        # círculo para el dron
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
    
    # Interpolar posiciones entre dos puntos
    def interpolate_positions(start_pos, end_pos, num_frames):
        positions = []
        for i in range(num_frames):
            t = i / num_frames
            x = int(start_pos[0] * (1 - t) + end_pos[0] * t)
            y = int(start_pos[1] * (1 - t) + end_pos[1] * t)
            positions.append((x, y))
        return positions
    
    print("Generando video de la ruta del dron...")
    route_centers = []
    for location in route:
        center = get_box_center(location)
        if center:
            polygon_id = get_polygon_by_position(location) if "-" in location else location
            route_centers.append((location, center, polygon_id))

    base_img = draw_all_boxes(img)
    
   
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
    
    # Definir tamaños base, mínimo y máximo para el dron
    base_drone_size = width // 40
    min_drone_size = width // 30  # Más pequeño para mayor dinamismo
    max_drone_size = width // 20  # Más grande para mayor dinamismo

    path_history = []
    if len(route_centers) > 0:
        path_history.append(route_centers[0][1])
    
    for i in range(len(route_centers) - 1):
        current_location, current_pos, current_polygon = route_centers[i]
        next_location, next_pos, next_polygon = route_centers[i + 1]
        
        print(f"Animando movimiento: {current_location} → {next_location}")
        

        if "-" in current_location:
            current_bbox = cell_dict_by_position[current_location]
        else:
            current_bbox = cell_dict_by_id[current_location]
            
        if "-" in next_location:
            next_bbox = cell_dict_by_position[next_location]
        else:
            next_bbox = cell_dict_by_id[next_location]
        
        # interpoliación de posiciones para movimiento suave
        positions = interpolate_positions(current_pos, next_pos, frames_between_points)
        
        for j, pos in enumerate(positions):
    
            progress = j / frames_between_points
            

            current_drone_size = calculate_dynamic_drone_size(
                current_bbox, next_bbox, progress, base_drone_size,
                min_factor=min_drone_size/base_drone_size,
                max_factor=max_drone_size/base_drone_size
            )
            

            if 0.1 < progress < 0.9:
                altitude_factor = 0.85 + 0.15 * np.sin(progress * np.pi)  # Parábola invertida
                current_drone_size = int(current_drone_size * altitude_factor)
            
            frame = base_img.copy()
            
            if len(path_history) > 1:
                for k in range(len(path_history) - 1):
                    cv2.line(frame, path_history[k], path_history[k + 1], (0, 100, 255), 2)
            

            cv2.line(frame, current_pos, next_pos, (0, 255, 255), 2)
            

            highlight_color = (0, 255, 255)  # Amarillo
            cv2.rectangle(frame, 
                         (current_bbox[0], current_bbox[1]), 
                         (current_bbox[2], current_bbox[3]), 
                         highlight_color, 3)
            cv2.rectangle(frame, 
                         (next_bbox[0], next_bbox[1]), 
                         (next_bbox[2], next_bbox[3]), 
                         highlight_color, 3)
            

            near_endpoint = j < frames_between_points * 0.1 or j > frames_between_points * 0.9
            
            frame = draw_drone_with_image(frame, pos, drone_img_path, current_drone_size, highlight=near_endpoint)
 
            if j == len(positions) - 1:
                path_history.append(pos)
                
            video_out.write(frame)
    
    # frame finales - mantener el último punto por unos segundos
    final_frame = base_img.copy()
    

    for i in range(len(path_history) - 1):
        cv2.line(final_frame, path_history[i], path_history[i + 1], (0, 100, 255), 3)
    

    final_drone_size = int(base_drone_size * 1.4)
    
    # dron en posición final usando la imagen
    final_frame = draw_drone_with_image(final_frame, path_history[-1], drone_img_path, final_drone_size, highlight=True)
    
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
    
    json_path= "44_Elementos_JDE.csv"

        # Cargar el JSON con los bounding boxes
    route= load_route_from_csv(json_path)
    print (route)
    create_dron_video_3d(route,44)
    #create_dron_video_3d_test(37)
