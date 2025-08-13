class EpcTranslator:
    def getData(data):
        if isinstance(data, str):
            epc_bytes = bytes.fromhex(data)
        # Verificar si data ya es un objeto bytes
        elif isinstance(data, bytes):
            epc_bytes = data
        else:
            raise TypeError("El argumento 'data' debe ser una cadena hexadecimal (str) o un objeto bytes.")
            epc_bytes = data
        translator = EpcTranslator(epc_bytes)
        epc_hex_formatted = translator.translate_to_hex()
        return epc_hex_formatted

    def __init__(self, epc_bytes):
        self.epc_bytes = epc_bytes

    def translate_to_hex(self):
        # Convertir los bytes a una cadena hexadecimal sin prefijo
        epc_hex = self.epc_bytes.hex()

        # Dividir la cadena hexadecimal en grupos de dos caracteres
        epc_hex_split = [epc_hex[i:i+2] for i in range(0, len(epc_hex), 2)]

        # Unir los grupos de dos caracteres con un espacio
        epc_hex_formatted = ' '.join(epc_hex_split)

        # Retornar la cadena formateada
        return epc_hex_formatted

if __name__ == '__main__':
    print("main")
    
    # Valor de la etiqueta RFID (EPC) en bytes
    epc_bytes = b'\xe2\x80\x11\x91\xa5\x03\x00e\xfe\xfa\xc7y~'

    # Crear una instancia de la clase EpcTranslator con el valor de la etiqueta RFID
    translator = EpcTranslator(epc_bytes)

    # Obtener la representación hexadecimal del EPC con grupos de dos caracteres
    epc_hex_formatted = translator.translate_to_hex()

    print("EPC en hexadecimal (grupos de 2):", epc_hex_formatted)