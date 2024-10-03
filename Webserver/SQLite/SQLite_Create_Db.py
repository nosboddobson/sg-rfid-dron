import sqlite3

db_name='inventario.db'
def crear_db_inventario():

    # Conectar a la base de datos (crea una nueva si no existe)
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Crear la tabla
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Inventario_Vuelos (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Nombre_Archivo TEXT,
            Fecha_Vuelo TEXT,
            N_elementos INTEGER,
            Estado_Inventario TEXT CHECK(Estado_Inventario IN ('Pendiente', 'OK'))
        )
    ''')

     # Crear la tabla
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Inventarios_JDE (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_Vuelo INTEGER,
            Fecha_Inventario TEXT,
            Elementos_OK INTEGER,
            Elementos_Faltantes INTEGER,
            Elementos_Sobrantes INTEGER,
            Porcentaje_Lectura REAL,
            NumeroConteo INTEGER,
            Sucursal TEXT,
            Ubicacion TEXT,
            TransactionId TEXT,
            FOREIGN KEY(ID_Vuelo) REFERENCES Inventario_Vuelos(ID)
        )
    ''')

    # Crear la tabla
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Elementos_JDE (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            EPC TEXT,
            Resultado TEXT CHECK(Resultado IN ('Ok', 'Faltante', 'Sobrante')),
            ID_Inventario INTEGER,
            Ubicacion TEXT,
            CodigoArticulo TEXT,
            FOREIGN KEY(ID_Inventario) REFERENCES Inventarios_JDE(ID)
        )
    ''')

    # Guardar los cambios
    conn.commit()

    # Cerrar la conexión
    conn.close()



if __name__ == "__main__":
# Llamar a la función para crear la tabla
    try :

       crear_db_inventario()
    except Exception as e:
       print(e)
    