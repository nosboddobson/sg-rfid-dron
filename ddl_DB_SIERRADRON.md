# DDL — DB_SIERRADRON

**Servidor origen:** `CJCSG-SQLDEV01`  
**Fecha extracción:** 2026-03-30 11:04:19  
**Tablas/Vistas:** 5

---


## dbo.Dron_Heartbeats  

| PK | Columna | Tipo | Nullable | Default | Identity |
|:--:|---------|------|:--------:|---------|:--------:|
|  | `HeartbeatTime` | DATETIME2(7) | YES |  |  |
| ✓ | `ID` | INT | NO |  | ✓ |
|  | `Source` | VARCHAR(255) | YES |  |  |

## dbo.Dron_Stop_Button  

| PK | Columna | Tipo | Nullable | Default | Identity |
|:--:|---------|------|:--------:|---------|:--------:|
| ✓ | `ID` | INT | NO |  | ✓ |
|  | `USUARIO` | NVARCHAR(255) | YES |  |  |
|  | `Fecha` | DATETIME2(7) | NO |  |  |

## dbo.Inventario_Vuelos  

| PK | Columna | Tipo | Nullable | Default | Identity |
|:--:|---------|------|:--------:|---------|:--------:|
| ✓ | `ID` | INT | NO |  | ✓ |
|  | `Nombre_Archivo` | NVARCHAR(255) | YES |  |  |
|  | `Fecha_Vuelo` | DATETIME | YES |  |  |
|  | `N_elementos` | INT | YES |  |  |
|  | `Tiempo_Vuelo` | INT | YES |  |  |
|  | `Estado_Inventario` | NVARCHAR(10) | YES |  |  |

## dbo.Inventarios_JDE  

| PK | Columna | Tipo | Nullable | Default | Identity |
|:--:|---------|------|:--------:|---------|:--------:|
| ✓ | `ID` | INT | NO |  | ✓ |
|  | `ID_Vuelo` | INT | YES |  |  |
|  | `Fecha_Inventario` | DATETIME | YES |  |  |
|  | `Elementos_OK` | INT | YES |  |  |
|  | `Elementos_Faltantes` | INT | YES |  |  |
|  | `Elementos_Sobrantes` | INT | YES |  |  |
|  | `Porcentaje_Lectura` | FLOAT(53) | YES |  |  |
|  | `NumeroConteo` | INT | YES |  |  |
|  | `Sucursal` | NVARCHAR(255) | YES |  |  |
|  | `Ubicacion` | NVARCHAR(255) | YES |  |  |
|  | `TransactionId` | NVARCHAR(255) | YES |  |  |
|  | `Imagen_Vuelo` | VARCHAR(255) | YES |  |  |
|  | `Video_Vuelo` | VARCHAR(255) | YES |  |  |

**Foreign Keys:**
- `ID_Vuelo` → `Inventario_Vuelos.ID` (constraint: `FK__Inventari__ID_Vu__276EDEB3`)

## dbo.Elementos_JDE  

| PK | Columna | Tipo | Nullable | Default | Identity |
|:--:|---------|------|:--------:|---------|:--------:|
| ✓ | `ID` | INT | NO |  | ✓ |
|  | `EPC` | NVARCHAR(255) | YES |  |  |
|  | `Resultado` | NVARCHAR(10) | YES |  |  |
|  | `ID_Inventario` | INT | YES |  |  |
|  | `Ubicacion` | NVARCHAR(255) | YES |  |  |
|  | `CodigoArticulo` | NVARCHAR(255) | YES |  |  |
|  | `Fecha_lectura` | DATETIME | YES |  |  |

**Foreign Keys:**
- `ID_Inventario` → `Inventarios_JDE.ID` (constraint: `FK__Elementos__ID_In__2C3393D0`)