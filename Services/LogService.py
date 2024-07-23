
import time
import pandas as pd


csv_Ejecuciones= "Api_Executions.csv"


def Guardar_Ejecucion_a_csv(start_time,end_time,Api,code):
    try:
        execution_time = end_time - start_time
        data = {'Api': Api, 'StartTime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)), 'ExecutionDuration': execution_time,'Code':code}
        df = pd.DataFrame(data, index=[0])
        df.to_csv(csv_Ejecuciones, index=False,mode='a', header=False)
    except Exception as e:
        print('Error Guardando registro de Ejecución: ' + str(e))


# Ejemplo de uso
if __name__ == "__main__":

    start_time = time.time()
    Api = "Ejemplo"
    time.sleep(5)
    end_time = time.time()
    Guardar_Ejecucion_a_csv(start_time,end_time,Api)
    print ("OK")
