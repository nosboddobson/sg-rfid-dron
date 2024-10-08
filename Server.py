import time
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import jsonschema
from Services import JDService, LogService as SaveExecutions
from Services import DronService
from Services import SQLite_Service
import os
import json 
import datetime



app = Flask(__name__)
load_dotenv(override=True)

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
        archivo_json=DronService.actualizar_estado_inventario(archivo_json)
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

'''
Defines a Flask route to handle POST requests for updating drone inventory. 
Calls an API to generate an inventory file, processes the file to update inventory status, and logs the execution details. 
Returns the updated inventory JSON if successful, or appropriate error messages if unsuccessful.

On success: JSON response {'OK': 'Inventario en JD Actualizado con Éxito'}, HTTP status 200.
On failure: JSON response with an error message, HTTP status 404 or 500.
'''
@app.route('/dron/actualizar-inventario', methods=['POST'])
def actualizar_inventario():

    start_time = time.time()
    
    #Obtener parametros del POST
    Sucursal = request.args.get('Sucursal', "SGMINA") #SGMIN valor por defecto si no viene parametro en la consulta
    Ubicacion = request.args.get('Ubicacion', "PT") #PF2 valor por defecto si no viene parametro en la consulta

    print(Sucursal + " ; " + Ubicacion)
    ID=request.args.get('ID')
    Tipo_Inventario=request.args.get('Tipo_Inventario')

    if Tipo_Inventario == "Completo":
        Ubicacion="PT"
    
    try:
        
        #LLamar API para que¡JD Edwards genere un archivo con el inventario
        if JDService.Generar_Conteo(Sucursal,Ubicacion) is not None:
            #obtenemos los valores retornados de Generar Conteo
           
            #Esperamos unos segundos para que el servidor genere el archivo con el inventario jsonout.txt
            time.sleep(10)

            print ("Conteo Solicitado OK")
            #Revisar si se la fecha del archivo disponoble es actual (> a la hora de inicio de ejecucion del codigo)
            if JDService.Archivo_Conteo_Generado_Nuevo(start_time):
               
                print ("Archivos de Conteo Existentes")
                # Comparamos inventario disponible con  obtenido desde Dron
                inventario_json,NumeroConteo,TransactionId= DronService.actualizar_estado_inventario()
                #print (inventario_json)
                #si resulta, entonces guardamos resultado como csv

                
                if inventario_json:
                    #Guardar Resultado de Inventario en csv
                    DronService.Guardar_json_como_csv(inventario_json,os.getenv('DRON_FOLDER_RESULTS'),Ubicacion)

                    #Devolvemos inventario Actualizado a JD
                    if JDService.Retorno_Datos_Conteo(inventario_json):
                        
                        print ("Retorno de Conteo OK")
                        #Generar Reporte 
                        JDService.Generar_Reporte_Conteo(NumeroConteo)
                        print ("Cierre de Conteo OK")
                        
                        end_time = time.time()
                        SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"actualizar-inventario",200)

                        #Actualizar DB
                        if (ID):
                           
                            SQLite_Service.Actuaizar_Estado_inventario_vuelos(int(ID))
                            resumen=SQLite_Service.Resumen_de_Conteo_desde_Json(inventario_json)
                            print (resumen)

                            ahora = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            #print (ahora)

                            SQLite_Service.insertar_inventario_jde(ID,ahora,resumen['OK Count'],resumen['FALTANTE Count'],resumen['Other Count'],resumen['Percentage OK'],NumeroConteo,Sucursal,Ubicacion,TransactionId)

                            print ("DB Actualizada con Exito")
                        return jsonify({'OK': 'Inventario en JD Actualizado con Éxito'}), 200 
                    
                    else:
                        end_time = time.time()
                        SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"actualizar-inventario",404)
                        return jsonify({'error': 'No fue posible Enviar Inventario a JD'}), 404 

                else:
                    end_time = time.time()
                    SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"actualizar-inventario",404)
                    return jsonify({'error': 'No fue posible Obtener Inventario desde JD'}), 404
            else:
                    end_time = time.time()
                    SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"actualizar-inventario",404)
                    return jsonify({'error': 'Archivo desde JD No Generado'}), 404    
            

        else:
            end_time = time.time()
            SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"actualizar-inventario",404)
            return jsonify({'error': 'No fue posible Obtener Inventario desde JD'}), 404
        
        #devolvemos el json con el resultado si todo salio bien
        return jsonify(inventario_json), 200
    except Exception as e:
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"actualizar-inventario",500)
        print ({'Error': str(e)})
        return jsonify({'Error': str(e)}), 500



@app.route('/api/data', methods=['POST'])
def post_data():
    new_data = request.json
    return jsonify(new_data), 201

'''
This code defines a Flask route that handles POST requests to the /upload endpoint. 
It processes file uploads, saves the file to a specified directory, logs the execution details, 
and returns appropriate responses based on the success or failure of the upload.

Outputs
On success: JSON response with a success message and filename, HTTP status 200.
On failure: JSON response with an error message, HTTP status 400 or 500.
'''
@app.route('/upload', methods=['POST'])
def upload_file():
    # Verifica si el archivo está en la solicitud
    start_time = time.time()

    if 'file' not in request.files:
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"Upload_File",400)
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Si el usuario no selecciona un archivo, el navegador puede enviar un archivo sin nombre
    if file.filename == '':
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"Upload_File",500)
        return jsonify({'error': 'No selected file'}), 400
    
    # Guarda el archivo en el directorio de subidas
    if file:
        filename = file.filename
        file.save(os.path.join(os.getenv('DRON_FOLDER'), filename)) #guardar Archivo

        SaveExecutions.Guardar_Recepcion_Archivos_Dron_a_csv(filename) #Actualizar Log en Carpeta de Archivos

        SQLite_Service.insertar_datos_inventario_vuelos (filename) #Guardar informacion en DB para Web

        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time,end_time,"Upload_File",200)
        return jsonify({'message': 'File successfully uploaded', 'filename': "1"}), 200



'''
This code defines a Flask route that handles POST requests to the /printer/<msg> endpoint.
It prints the message provided in the URL and returns a JSON response indicating success 
or an error message if an exception occurs.

Outputs
On success: JSON response {'message': 'ok'} with a 200 status code.
On failure: JSON response {'Error': <error_message>} with a 500 status code.

'''
@app.route('/printer/<msg>', methods=['POST'])
def show_message(msg):
    try:
        print(msg)
        return jsonify({'message': 'ok'}), 200
    except Exception as e:
        return jsonify({'Error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5100)