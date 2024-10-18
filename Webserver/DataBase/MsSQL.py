import pyodbc

#runas /user:DOMAIN\Username /savecred  "python .\Webserver\DataBase\MsSQL.py"


# Connection details for SQL Server
server = 'CJCSG-SQLDEV01'  # e.g., 'localhost\SQLEXPRESS' or IP
database = 'DB_SIERRADRON'  # Your SQL Server database name


def crear_db_inventario():

    # Establish connection to SQL Server
    conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes')
    cursor = conn.cursor()

    # Create the Inventario_Vuelos table
    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Inventario_Vuelos')
        CREATE TABLE Inventario_Vuelos (
            ID INT IDENTITY(1,1) PRIMARY KEY,
            Nombre_Archivo NVARCHAR(255),
            Fecha_Vuelo DATETIME,
            N_elementos INT,
            Tiempo_Vuelo INT,
            Estado_Inventario NVARCHAR(10) CHECK(Estado_Inventario IN ('Pendiente', 'OK'))
        )
    ''')

    # Create the Inventarios_JDE table
    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Inventarios_JDE')
        CREATE TABLE Inventarios_JDE (
            ID INT IDENTITY(1,1) PRIMARY KEY,
            ID_Vuelo INT,
            Fecha_Inventario DATETIME,
            Elementos_OK INT,
            Elementos_Faltantes INT,
            Elementos_Sobrantes INT,
            Porcentaje_Lectura FLOAT,
            NumeroConteo INT,
            Sucursal NVARCHAR(255),
            Ubicacion NVARCHAR(255),
            TransactionId NVARCHAR(255),
            FOREIGN KEY(ID_Vuelo) REFERENCES Inventario_Vuelos(ID)
        )
    ''')

    # Create the Elementos_JDE table
    cursor.execute('''
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Elementos_JDE')
        CREATE TABLE Elementos_JDE (
            ID INT IDENTITY(1,1) PRIMARY KEY,
            EPC NVARCHAR(255),
            Resultado NVARCHAR(10) CHECK(Resultado IN ('OK', 'FALTANTE', 'SOBRANTE')),
            ID_Inventario INT,
            Ubicacion NVARCHAR(255),
            CodigoArticulo NVARCHAR(255),
            FOREIGN KEY(ID_Inventario) REFERENCES Inventarios_JDE(ID)
        )
    ''')

    # Commit changes
    conn.commit()

    # Close the connection
    conn.close()

if __name__ == "__main__":
    # Try to create the database tables
    try:
        crear_db_inventario()
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error: {e}")
