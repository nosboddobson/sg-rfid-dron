import time
from flask import Flask, jsonify, request
import jsonschema
from Services import LogService as SaveExecutions
from Services import ActualizarInventarioService
import os
import json 
from datetime import datetime



app = Flask(__name__)


"""
This code defines a Flask route that handles POST requests to the /AssignmentOperators/ endpoint. 
It retrieves JSON data from the request, processes it using the make_assignment function from the AssignmentService, 
and returns a confirmation message.

In the front end, when the operator press "Load Video" it sends a json with the Operator asignations to the endpoint. 
Now the endpoint takes the json and saves it as a csv in the pc, and then creates a video with the asignations 
and then saves it in Sharepoint so the operator can download the video.

"""
@app.route('/test')
def hello_world():
    start_time = time.time()
    end_time = time.time()
    SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"test",200)
    return '¡Prueba de Api Exitosa!'

'''
Defines a Flask route to handle POST requests for updating inventory status of drones. 
Validates the JSON data received against a predefined JSON schema. Logs the execution details and returns appropriate responses 
based on validation results.
'''
@app.route('/dron/actualizar-estado-inventario', methods=['POST'])
def actualizar_estado_inventario():
   
    json_schema= {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "Inventario": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                "BatchNumber": {"type": "string"},
                "Sequence": {"type": "string"},
                "NumeroConteo": {"type": "integer"},
                "Bodega": {"type": "string"},
                "Ubicacion": {"type": "string"},
                "NumeroEtiqueta": {"type": "string"},
                "CodigoArticulo": {"type": "string"},
                "CoordenadaX": {"type": "string"},
                "CoordenadaY": {"type": "string"},
                "TransactionId": {"type": "string"},
                "TotalBatch": {"type": "string"},
                "CoordenadaZ": {"type": "string"}
                },
                "required": [
                "BatchNumber",
                "Sequence",
                "NumeroConteo",
                "Bodega",
                "Ubicacion",
                "NumeroEtiqueta",
                "CodigoArticulo",
                "CoordenadaX",
                "CoordenadaY",
                "TransactionId",
                "TotalBatch",
                "CoordenadaZ"
                ]
            }
            }
        },
        "required": ["Inventario"]
    }

    #Get json sent by Post
    start_time = time.time()
    archivo_json = request.get_json()
    
    # Intenta abrir el archivo JSON
    try:
        jsonschema.validate(instance=archivo_json, schema=json_schema)
        # Devuelve el JSON como respuesta
        archivo_json=ActualizarInventarioService.actualizar_estado_inventario(archivo_json)
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"actualizar-estado-inventario",200)
        return jsonify(archivo_json)
    except jsonschema.exceptions.ValidationError as e:
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"actualizar-estado-inventario",404)
        return jsonify({'error': 'Esquema de Archivo no Valido!.', 'Campos necesarios': json_schema["properties"]["Inventario"]["items"]["required"]}), 404
    except Exception as e:
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"actualizar-estado-inventario",500)
        return jsonify({'Error': str(e)}), 500

    
def utc_time():
    return datetime.now().strftime('%Y-%m-%d_%H_%M_%S')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)