# Documentación de API con Swagger

## Descripción
La API Sierra Dron ahora cuenta con documentación automática generada con **Swagger** (OpenAPI 2.0) usando **Flasgger**.

## Acceso a la documentación

Una vez que el servidor esté ejecutándose, puedes acceder a la documentación interactiva en:

### Swagger UI
```
http://localhost:5100/apidocs
```

### ReDoc (Documentación alternativa)
```
http://localhost:5100/redoc
```

### Especificación OpenAPI en JSON
```
http://localhost:5100/swagger.json
```

## Características de la documentación

La documentación incluye:

- ✅ **Descripción detallada** de cada endpoint
- ✅ **Parámetros de entrada** con sus tipos y validaciones
- ✅ **Esquemas de respuesta** para cada código de estado HTTP
- ✅ **Ejemplos de uso** para cada endpoint
- ✅ **Interfaz interactiva** para probar los endpoints
- ✅ **Códigos de estado HTTP** documentados (200, 201, 400, 404, 500)

## Endpoints documentados

### Testing
- `GET /test` - Prueba simple de conectividad

### Dron - Inventario
- `POST /dron/actualizar-estado-inventario` - Actualiza el estado del inventario
- `POST /dron/actualizar-inventario` - Orquesta el proceso completo de inventario
- `POST /dron/eliminar-inventario` - Elimina un registro de inventario

### File Upload
- `POST /upload` - Carga archivos CSV desde el dron

### Keep Alive
- `POST /printer/<msg>` - Verifica conectividad del dron

### Data
- `POST /api/data` - Endpoint genérico para recibir datos JSON

### Testing - JD Folder
- `POST /dron/TestJDFolder` - Verifica conexión a carpeta compartida de JD Edwards

## Cómo usar Swagger UI

1. **Inicia el servidor:**
   ```bash
   python Server.py
   ```

2. **Abre tu navegador:**
   - Ve a `http://localhost:5100/apidocs`

3. **Prueba los endpoints:**
   - Haz clic en cualquier endpoint para expandirlo
   - Haz clic en "Try it out"
   - Completa los parámetros requeridos
   - Haz clic en "Execute" para enviar la solicitud
   - Visualiza la respuesta y códigos de estado

## Ejemplo de prueba

### Probar el endpoint `/test`
1. En Swagger UI, busca el endpoint `GET /test`
2. Haz clic en "Try it out"
3. Haz clic en "Execute"
4. Deberías recibir la respuesta: `"¡Prueba de Api Exitosa!"`

### Probar carga de archivos
1. En Swagger UI, busca el endpoint `POST /upload`
2. Haz clic en "Try it out"
3. Selecciona un archivo CSV
4. Haz clic en "Execute"
5. Recibirás confirmación de la carga

## Información de configuración

La API está configurada con los siguientes detalles:

- **Título:** Sierra Dron API
- **Descripción:** API para gestión de inventario de drones y sincronización con JD Edwards
- **Versión:** 1.0.0
- **Host:** localhost:5100
- **Esquemas:** HTTP, HTTPS
- **Autor:** Soporte Sierra

## Instalación de dependencias

Asegúrate de que todas las dependencias estén instaladas:

```bash
pip install flasgger
# o instala desde requirements.txt
pip install -r requirements.txt
```

## Exportar especificación OpenAPI

Para descargar la especificación completa en formato JSON:

```bash
curl http://localhost:5100/swagger.json > swagger.json
```

Esta especificación puede usarse en herramientas como Postman, Insomnia, o generadores de código.

## Solución de problemas

### Swagger UI no carga
- Asegúrate de que el servidor está corriendo en `localhost:5100`
- Verifica que Flasgger está correctamente instalado: `pip show flasgger`
- Reinicia el servidor

### Los endpoints no aparecen
- Asegúrate de que los docstrings en los endpoints tienen el formato YAML correcto
- Verifica que los endpoints tienen el formato `--- yaml` en el docstring
- Reinicia el servidor

## Más información

Para más información sobre Flasgger y Swagger:
- [Documentación de Flasgger](https://flasgger.readthedocs.io/)
- [OpenAPI 2.0 Specification](https://swagger.io/specification/v2/)
