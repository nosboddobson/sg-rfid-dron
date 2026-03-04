# Test Suite para predict_inventory_zone()

## Descripción

Este directorio contiene tests para debuggear el endpoint `/inventarios-pendientes` y la función `predict_inventory_zone()`.

El problema investigado:
- **EPCs en archivo**: `e2 80 11 91 a5 04 00 6d 1c 88 a9 6` (con espacios)
- **EPCs en BD**: `E2801191A504006D1C8CE40B` (sin espacios, mayúsculas)
- **Pregunta**: ¿Por qué no encuentra los EPCs después de limpiar espacios?

## Test Principal: `test_predict_zone.py`

### ¿Qué hace?

El script ejecuta 4 tests secuenciales para debuggear el problema:

#### **TEST 1: API Endpoint**
- Llama a `GET /inventarios-pendientes`
- Busca el inventario con ID 1562
- Muestra:
  - Zona predicha
  - Confianza de predicción
  - Desglose de zonas

#### **TEST 2: Lectura de Archivo CSV**
- Obtiene el nombre del archivo desde Inventario_Vuelos
- Abre el archivo CSV desde `Dron_Folder`
- Extrae EPCs raw (como están en el archivo)
- Extrae EPCs limpios (después de `strip()` y `upper()`)
- Compara los primeros 10 en ambos formatos

#### **TEST 3: Búsqueda en Base de Datos**
- Busca cada EPC en la tabla Elementos_JDE
- Muestra qué EPCs se encuentran y cuáles no
- Muestra las ubicaciones (zonas) encontradas
- Analiza todos los EPCs y calcula distribución de zonas

#### **TEST 4: Comparación de Formatos**
- Compara el ejemplo que proporcionó el usuario
- EPC BD: `E2801191A504006D1C8CE40B`
- EPC Archivo: `e2 80 11 91 a5 04 00 6d 1c 88 a9 6`
- Muestra qué sucede después de limpiar
- Hace comparación byte a byte

### Cómo Ejecutar

```bash
# Navegar al directorio del proyecto
cd d:\dev\sg-rfid-dron

# Opción 1: Ejecutar directamente
python test/test_predict_zone.py

# Opción 2: Con PowerShell
cd .\test
python test_predict_zone.py

# Opción 3: Desde VS Code
# Abrir terminal en test/ y ejecutar
python test_predict_zone.py
```

### Requisitos Previos

1. **Servidor debe estar ejecutándose**:
   ```bash
   # Terminal 1: Iniciar Server.py
   python Server.py
   ```

2. **Variables de entorno configuradas** (`.env`):
   - `DB_DRON_SERVER`
   - `DB_DRON_DATABASE`
   - `DB_DRON_USERNAME`
   - `DB_DRON_PASSWORD`
   - `Dron_Folder` (ruta a carpeta de archivos CSV)

3. **Inventario 1562 debe existir**:
   - En tabla `Inventario_Vuelos`
   - Con archivo asociado en `Dron_Folder`
   - Con EPCs en tabla `Elementos_JDE`

### Output Esperado

```
================================================================================
                  TEST 1: Llamando a /inventarios-pendientes
================================================================================

✓ Endpoint respondió correctamente
ℹ Total inventarios pendientes: 15

✓ Inventario ID 1562 encontrado

Datos del Inventario:
  - Fecha Vuelo: 2026-01-31
  - N° Elementos: 300
  - Tiempo Vuelo: 1200s
  - Zona Predicha: PF2
  - Confianza: 83.5
  - Desglose: {
    "PF1": 5.0,
    "PF2": 83.5,
    "PF5": 11.5
}

================================================================================
                         TEST 2: Leyendo archivo CSV
================================================================================

✓ Nombre de archivo obtenido: 2026-01-31_18_22_41_dron.csv
ℹ Ruta completa: D:\SierraDron-Files\2026-01-31_18_22_41_dron.csv
✓ Archivo encontrado
✓ CSV leído correctamente
ℹ Total de filas en CSV: 300
ℹ Columnas en CSV: ['EPC', 'Timestamp', 'Localtime', ...]

Primeros 10 EPCs en archivo (raw):
  1: 'e2 80 11 91 a5 04 00 6d 1c 88 a9 6'
  2: 'a1 b2 c3 d4 e5 f6 01 23 45 67 89 a'
  ...

Primeros 10 EPCs limpios (tras strip y upper):
  1: 'E2801191A504006D1C88A96'
  2: 'A1B2C3D4E5F60123456789A'
  ...

✓ Total de EPCs válidos después de limpiar: 285

================================================================================
                      TEST 3: Buscando EPCs en BD
================================================================================

ℹ Buscando 285 EPCs en BD...

Resultado de búsqueda (primeros 20 EPCs):

   1. ENCONTRADO: EPC='E2801191A504006D1C88A96' → Ubicacion='PF2' (ID=1000)
   2. ENCONTRADO: EPC='A1B2C3D4E5F60123456789A' → Ubicacion='PF2' (ID=1001)
   3. NO ENCONTRADO: EPC='...'
   ...

Resumen de búsqueda en primeros 20 EPCs:
✓ EPCs encontrados: 18
⚠ EPCs no encontrados: 2

Zonas encontradas:
  - PF2: 15 (83.3%)
  - PF1: 2 (11.1%)
  - PF5: 1 (5.6%)

================================================================================
                    CONCLUSIONES Y RECOMENDACIONES
================================================================================

✓ La predicción de zona funcionó correctamente
```

### Interpretación de Resultados

#### ✓ **Éxito**: Zona predicha correctamente
- EPCs se encuentran en la BD
- Distribución de zonas está clara (>70% de una zona)
- Pero verificar que el formato coincida exactamente

#### ⚠ **Parcial**: Algunos EPCs no se encuentran
- Algunos EPCs del archivo no están en la BD
- Posibles causas:
  - EPCs no fueron insertados en BD
  - Épocas diferentes de datos
  - Formato de EPC diferente

#### ✗ **Error**: Ningún EPC se encuentra
- Los EPCs no coinciden con los de la BD
- Verificar:
  - ¿El formato del EPC es diferente? (revisión byte a byte)
  - ¿Los espacios se limpian correctamente?
  - ¿El archivo es del inventario 1562?
  - ¿El inventario 1562 existe en la BD?

### Debugging Avanzado

Si el test muestra que **ningún EPC se encuentra**, ejecuta esto para inspeccionar:

```python
# Abrir Python interactivo
python

# En Python:
>>> from Services import MsSQL_Service as db
>>> import os
>>> from dotenv import load_dotenv
>>> load_dotenv()

# Ver primeros EPCs en BD para el inventario 1562:
>>> conn = db.get_db_connection()
>>> sql = "SELECT TOP 5 EPC FROM Elementos_JDE WHERE ID_Inventario IN (SELECT ID FROM Inventarios_JDE WHERE ID_Vuelo=1562)"
>>> df = db.execute_sql_query(sql, conn)
>>> print(df['EPC'].tolist())

# Ver primeros EPCs del archivo:
>>> import pandas as pd
>>> dron_folder = os.getenv('Dron_Folder')
>>> # Encontrar el archivo del inventario 1562
>>> sql2 = "SELECT Nombre_Archivo FROM Inventario_Vuelos WHERE ID=1562"
>>> df2 = db.execute_sql_query(sql2, conn)
>>> filename = df2.iloc[0]['Nombre_Archivo']
>>> df_file = pd.read_csv(f"{dron_folder}/{filename}")
>>> print(df_file['EPC'].head().tolist())

# Comparar directamente:
>>> epc_bd = "E2801191A504006D1C8CE40B"
>>> epc_file = "e2 80 11 91 a5 04 00 6d 1c 88 a9 6"
>>> epc_file_clean = epc_file.strip().upper().replace(' ', '')
>>> print(f"BD:    {epc_bd}")
>>> print(f"File:  {epc_file_clean}")
>>> print(f"Match: {epc_bd == epc_file_clean}")
```

### Archivos Incluidos

- `test_predict_zone.py` - Script principal de test (este archivo)
- `README.md` - Este archivo con instrucciones

### Próximos Pasos

Si el test falla, documentar:
1. ¿Qué test falla exactamente?
2. ¿Cuál es el output específico del error?
3. ¿Cuántos EPCs se encuentran vs cuántos no?
4. ¿Hay diferencias en los formatos de EPC?

Esto ayudará a identificar exactamente dónde está el problema.
