# ==============================================================================
# Módulo: EpcTranslator.py
#
# Descripción:
# Este módulo define la clase `EpcTranslator`, que se especializa en la
# traducción de los datos de una etiqueta RFID (EPC) a un formato legible
# para humanos. Su función principal es convertir la representación en bytes
# del EPC a una cadena hexadecimal formateada, dividida en grupos de dos
# caracteres para facilitar su lectura y análisis.
# ==============================================================================

class EpcTranslator:
    """
    Clase para traducir los datos EPC (Electronic Product Code) de una
    etiqueta RFID a un formato hexadecimal legible.

    El EPC es un identificador único que se utiliza en la tecnología RFID.
    Esta clase facilita su manipulación y visualización al convertirlo de
    su representación binaria a una cadena de texto formateada.
    """

    def __init__(self, epc_bytes: bytes):
        """
        Inicializa una instancia de EpcTranslator.

        Args:
            epc_bytes (bytes): La representación en bytes del EPC.
        """
        self.epc_bytes = epc_bytes

    @staticmethod
    def getData(data: bytes | str) -> str:
        """
        Método estático para traducir datos EPC a una cadena hexadecimal formateada.

        Este método puede aceptar tanto una cadena hexadecimal como un objeto de
        tipo bytes y se encarga de realizar la conversión y el formateo. Es útil
        como un punto de entrada único para la traducción de EPCs.

        Args:
            data (bytes | str): El EPC a traducir, que puede ser una cadena
                                hexadecimal o una secuencia de bytes.

        Returns:
            str: La representación hexadecimal del EPC, formateada con espacios.

        Raises:
            TypeError: Si el argumento 'data' no es de tipo 'str' o 'bytes'.
        """
        if isinstance(data, str):
            epc_bytes = bytes.fromhex(data)
        elif isinstance(data, bytes):
            epc_bytes = data
        else:
            raise TypeError("El argumento 'data' debe ser una cadena hexadecimal (str) o un objeto bytes.")
        
        translator = EpcTranslator(epc_bytes)
        return translator.translate_to_hex()

    def translate_to_hex(self) -> str:
        """
        Convierte los bytes del EPC a una cadena hexadecimal formateada.

        El método toma la secuencia de bytes almacenada en el objeto y la
        convierte a una cadena hexadecimal, la cual es luego dividida en
        grupos de dos caracteres separados por un espacio.

        Returns:
            str: Una cadena formateada que representa el EPC en hexadecimal.
        """
        epc_hex = self.epc_bytes.hex()
        epc_hex_split = [epc_hex[i:i+2] for i in range(0, len(epc_hex), 2)]
        epc_hex_formatted = ' '.join(epc_hex_split)
        return epc_hex_formatted

# ------------------------------------------------------------------------------
# Ejemplo de Uso
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    print("--- Ejemplo de uso de EpcTranslator ---")
    
    # Valor de la etiqueta RFID (EPC) en bytes
    epc_bytes = b'\xe2\x80\x11\x91\xa5\x03\x00e\xfe\xfa\xc7y~'

    # 1. Usando el método de instancia
    translator = EpcTranslator(epc_bytes)
    epc_hex_formatted_instance = translator.translate_to_hex()
    print(f"EPC traducido (desde instancia): {epc_hex_formatted_instance}")

    # 2. Usando el método estático getData
    epc_hex_formatted_static = EpcTranslator.getData(epc_bytes)
    print(f"EPC traducido (desde método estático): {epc_hex_formatted_static}")
    
    # Ejemplo con una cadena hexadecimal
    epc_hex_string = 'e2801191a5030065fefac7797e'
    epc_hex_formatted_from_string = EpcTranslator.getData(epc_hex_string)
    print(f"EPC traducido (desde cadena hex): {epc_hex_formatted_from_string}")