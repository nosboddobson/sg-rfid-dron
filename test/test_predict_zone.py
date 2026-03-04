"""
Test Script para Debuggear bug de EPC Matching en predict_inventory_zone()

Este script testea el endpoint /inventarios-pendientes con ID 1562
y debuggea por qué no encuentra los EPCs en la base de datos.

Problemas conocidos:
- EPC en archivo: e2 80 11 91 a5 04 00 6d 1c 88 a9 6 (con espacios)
- EPC en BD: E2801191A504006D1C8CE40B (sin espacios)
- La limpieza de espacios debe funcionar, pero hay discrepancias en los valores reales

Uso:
    python test_predict_zone.py
"""

import requests
import json
import pandas as pd
import os
from dotenv import load_dotenv
import sys

# Añadir el directorio padre al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Services import MsSQL_Service as dbService

# Configuración
API_URL = "http://10.185.36.30:5100"
INVENTARIO_ID = 1579
DRON_FOLDER = os.getenv('DRON_FOLDER', 'D:\\SierraDron-Files')

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}{title:^80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

def print_success(msg):
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}✗ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ {msg}{Colors.ENDC}")

def test_api_endpoint():
    """Test 1: Llama al endpoint /inventarios-pendientes"""
    print_header(f"TEST 1: Llamando a /inventarios-pendientes")
    
    try:
        response = requests.get(f"{API_URL}/inventarios-pendientes")
        
        if response.status_code != 200:
            print_error(f"HTTP Error {response.status_code}")
            return None
        
        data = response.json()
        print_success(f"Endpoint respondió correctamente")
        print_info(f"Total inventarios pendientes: {data['count']}")
        
        # Buscar nuestro inventario
        inventario = None
        for inv in data['inventarios']:
            if inv['ID'] == INVENTARIO_ID:
                inventario = inv
                break
        
        if not inventario:
            print_error(f"No se encontró inventario con ID {INVENTARIO_ID}")
            return None
        
        print_success(f"Inventario ID {INVENTARIO_ID} encontrado")
        print(f"\n{Colors.BOLD}Datos del Inventario:{Colors.ENDC}")
        print(f"  - Fecha Vuelo: {inventario['Fecha_Vuelo']}")
        print(f"  - N° Elementos: {inventario['N_Elementos']}")
        print(f"  - Tiempo Vuelo: {inventario['Tiempo_Vuelo']}s")
        print(f"  - Zona Predicha: {Colors.OKGREEN if inventario['predicted_zone'] else Colors.FAIL}{inventario['predicted_zone']}{Colors.ENDC}")
        print(f"  - Confianza: {inventario['zone_confidence']}")
        print(f"  - Desglose: {json.dumps(inventario['zone_breakdown'], indent=4)}")
        
        return inventario
        
    except Exception as e:
        print_error(f"Error en API: {str(e)}")
        return None

def test_file_reading():
    """Test 2: Lee el archivo CSV y extrae EPCs"""
    print_header(f"TEST 2: Leyendo archivo CSV del Inventario {INVENTARIO_ID}")
    
    try:
        # Obtener nombre del archivo
        conn = dbService.get_db_connection()
        sql = 'SELECT Nombre_Archivo FROM Inventario_Vuelos WHERE ID = ?'
        df_file = dbService.execute_sql_query(sql, conn, params=(INVENTARIO_ID,))
        dbService.close_connection(conn)
        
        if df_file is None or len(df_file) == 0:
            print_error(f"No se encontró archivo para ID {INVENTARIO_ID} en BD")
            return None
        
        filename = df_file.iloc[0]['Nombre_Archivo']
        print_success(f"Nombre de archivo obtenido: {filename}")
        
        # Construir ruta
        file_path = os.path.join(DRON_FOLDER, filename)
        print_info(f"Ruta completa: {file_path}")
        
        if not os.path.exists(file_path):
            print_error(f"Archivo no existe en disco")
            return None
        
        print_success(f"Archivo encontrado")
        
        # Leer CSV
        try:
            df_csv = pd.read_csv(file_path)
        except Exception as e:
            print_error(f"Error leyendo CSV: {str(e)}")
            return None
        
        print_success(f"CSV leído correctamente")
        print_info(f"Total de filas en CSV: {len(df_csv)}")
        print_info(f"Columnas en CSV: {list(df_csv.columns)}")
        
        if 'EPC' not in df_csv.columns:
            print_error("Columna 'EPC' no encontrada en CSV")
            return None
        
        # Mostrar primeros EPCs del archivo
        print(f"\n{Colors.BOLD}Primeros 10 EPCs en archivo (raw):{Colors.ENDC}")
        for i, epc in enumerate(df_csv['EPC'].head(10).values):
            print(f"  {i+1}: '{epc}'")
        
        # Limpiar EPCs: convertir a string, remover espacios y convertir a mayúsculas
        epcs_cleaned = (df_csv['EPC']
            .astype(str)  # Convertir a string (convierte NaN a 'nan')
            .str.strip()  # Remover espacios
            .str.upper()  # Convertir a mayúsculas
            .str.replace(' ', '')  # Remover espacios internos
            .tolist())
        
        # Filtrar valores inválidos: vacíos, 'NAN', 'NONE', o muy cortos
        epcs_cleaned = [
            e for e in epcs_cleaned 
            if e and e != 'NAN' and e != 'NONE' and len(e.strip()) > 5
        ]
        
        print(f"\n{Colors.BOLD}Primeros 10 EPCs limpios (tras limpieza robusta):{Colors.ENDC}")
        for i, epc in enumerate(epcs_cleaned[:10]):
            print(f"  {i+1}: '{epc}'")
        
        print_success(f"Total de EPCs válidos después de limpiar: {len(epcs_cleaned)}")
        
        return {
            'filename': filename,
            'csv_data': df_csv,
            'epcs_cleaned': epcs_cleaned
        }
        
    except Exception as e:
        print_error(f"Error leyendo archivo: {str(e)}")
        return None

def test_epc_database_matching(file_data):
    """Test 3: Busca EPCs del archivo en la BD"""
    print_header(f"TEST 3: Buscando EPCs en Base de Datos")
    
    if not file_data:
        print_error("No hay datos de archivo para buscar")
        return
    
    epcs_cleaned = file_data['epcs_cleaned']
    
    try:
        conn = dbService.get_db_connection()
        
        print_info(f"Buscando {len(epcs_cleaned)} EPCs en BD...")
        
        found_count = 0
        not_found_count = 0
        zone_counts = {}
        
        # Buscar primeros 20 EPCs para debugging
        sample_epcs = epcs_cleaned[:20]
        
        print(f"\n{Colors.BOLD}Resultado de búsqueda (primeros 20 EPCs):{Colors.ENDC}\n")
        
        for i, epc in enumerate(sample_epcs, 1):
            sql_find = '''
                SELECT TOP 1 ej.ID_Inventario, ij.Ubicacion 
                FROM Elementos_JDE ej
                JOIN Inventarios_JDE ij ON ej.ID_Inventario = ij.ID
                WHERE ej.EPC = ?
                ORDER BY ej.ID_Inventario DESC
            '''
            
            df_found = dbService.execute_sql_query(sql_find, conn, params=(epc,))
            
            if df_found is not None and len(df_found) > 0:
                ubicacion = df_found.iloc[0]['Ubicacion']
                id_inventario = df_found.iloc[0]['ID_Inventario']
                zone_counts[ubicacion] = zone_counts.get(ubicacion, 0) + 1
                print(f"  {i:2d}. ENCONTRADO: EPC='{epc}' → Ubicacion='{ubicacion}' (ID_Inventario={id_inventario})")
                found_count += 1
            else:
                print(f"  {i:2d}. NO ENCONTRADO: EPC='{epc}'")
                not_found_count += 1
        
        dbService.close_connection(conn)
        
        print(f"\n{Colors.BOLD}Resumen de búsqueda en primeros 20 EPCs:{Colors.ENDC}")
        print_success(f"EPCs encontrados: {found_count}")
        print_warning(f"EPCs no encontrados: {not_found_count}")
        
        if zone_counts:
            print(f"\n{Colors.BOLD}Zonas encontradas:{Colors.ENDC}")
            for zona, count in sorted(zone_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / found_count * 100) if found_count > 0 else 0
                print(f"  - {zona}: {count} ({percentage:.1f}%)")
        
        # Analizar todas los EPCs (no solo los primeros 20)
        print(f"\n{Colors.BOLD}Analizando TODOS los {len(epcs_cleaned)} EPCs...{Colors.ENDC}")
        
        conn = dbService.get_db_connection()
        found_total = 0
        zone_counts_all = {}
        
        for epc in epcs_cleaned:
            sql_find = '''
                SELECT TOP 1 ej.ID_Inventario, ij.Ubicacion 
                FROM Elementos_JDE ej
                JOIN Inventarios_JDE ij ON ej.ID_Inventario = ij.ID
                WHERE ej.EPC = ?
                ORDER BY ej.ID_Inventario DESC
            '''
            
            df_found = dbService.execute_sql_query(sql_find, conn, params=(epc,))
            
            if df_found is not None and len(df_found) > 0:
                ubicacion = df_found.iloc[0]['Ubicacion']
                zone_counts_all[ubicacion] = zone_counts_all.get(ubicacion, 0) + 1
                found_total += 1
        
        dbService.close_connection(conn)
        
        print_success(f"EPCs encontrados en total: {found_total} de {len(epcs_cleaned)}")
        
        if zone_counts_all:
            print(f"\n{Colors.BOLD}Distribución total de zonas:{Colors.ENDC}")
            for zona, count in sorted(zone_counts_all.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / found_total * 100) if found_total > 0 else 0
                print(f"  - {zona}: {count} ({percentage:.1f}%)")
        else:
            print_error("Ningún EPC del archivo fue encontrado en la BD")
            
    except Exception as e:
        print_error(f"Error buscando EPCs: {str(e)}")

def test_epc_format_comparison():
    """Test 4: Compara formatos de EPC"""
    print_header("TEST 4: Comparación de Formatos de EPC")
    
    # Ejemplo que proporcionó el usuario
    epc_bd_example = "E2801191A504006D1C8CE40B"
    epc_file_example = "e2 80 11 91 a5 04 00 6d 1c 88 a9 6"
    
    print(f"EPC en BD (ejemplo):      '{epc_bd_example}'")
    print(f"EPC en archivo (ejemplo): '{epc_file_example}'")
    
    # Limpiar con el mismo método
    epc_cleaned = epc_file_example.strip().upper()
    epc_cleaned_no_spaces = epc_cleaned.replace(' ', '')
    
    print(f"\nDespués de strip + upper: '{epc_cleaned}'")
    print(f"Después de remover espacios: '{epc_cleaned_no_spaces}'")
    
    print(f"\n{Colors.BOLD}Análisis:{Colors.ENDC}")
    
    if epc_cleaned_no_spaces == epc_bd_example:
        print_success("Los valores coinciden después de limpiar espacios")
    else:
        print_error("Los valores NO coinciden incluso después de limpiar espacios")
        print_warning(f"Esperado: {epc_bd_example}")
        print_warning(f"Obtenido: {epc_cleaned_no_spaces}")
        
        # Mostrar diferencias
        print(f"\n{Colors.BOLD}Diferencias byte a byte:{Colors.ENDC}")
        max_len = max(len(epc_bd_example), len(epc_cleaned_no_spaces))
        for i in range(0, max_len, 2):
            bd_byte = epc_bd_example[i:i+2] if i < len(epc_bd_example) else "--"
            file_byte = epc_cleaned_no_spaces[i:i+2] if i < len(epc_cleaned_no_spaces) else "--"
            match = "✓" if bd_byte == file_byte else "✗"
            print(f"  Byte {i//2}: BD={bd_byte}  Archivo={file_byte}  {match}")

def main():
    print_header("SCRIPT DE TEST: predict_inventory_zone() - ID 1562")
    print_info("Debuggeando por qué no encuentra EPCs en la base de datos")
    print_info("Verificando: EPC en BD vs EPC en archivo")
    
    print("\n" + "="*80)
    
    # Test 1: API Endpoint
    inventario = test_api_endpoint()
    
    # Test 2: Lectura de archivo
    file_data = test_file_reading()
    
    # Test 3: Búsqueda en BD
    if file_data:
        test_epc_database_matching(file_data)
    
    # Test 4: Comparación de formatos
    test_epc_format_comparison()
    
    print("\n" + "="*80)
    print_header("CONCLUSIONES Y RECOMENDACIONES")
    
    if inventario and inventario['predicted_zone']:
        print_success("La predicción de zona funcionó correctamente")
    else:
        print_warning("No se encontró zona predicha. Posibles causas:")
        print("  1. Los EPCs del archivo NO coinciden con los de la BD (formato diferente)")
        print("  2. El archivo no está siendo leído correctamente")
        print("  3. La limpieza de espacios no es suficiente")
        print("  4. Los EPCs son completamente diferentes")

if __name__ == "__main__":
    load_dotenv(override=True)
    main()
