#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para probar el endpoint /inventarios-pendientes
Verifica que el servicio NSSM puede procesar la solicitud sin reiniciarse
"""

import requests
import time
import sys

API_URL = "http://10.185.36.30:5100"
ENDPOINT = "/inventarios-pendientes"

def test_endpoint():
    """Prueba el endpoint varias veces para verificar estabilidad del servicio"""
    
    print("=" * 80)
    print("[TEST] Iniciando pruebas del endpoint /inventarios-pendientes")
    print(f"[TEST] URL: {API_URL}{ENDPOINT}")
    print("=" * 80)
    
    success_count = 0
    error_count = 0
    
    for attempt in range(1, 6):  # 5 intentos
        try:
            print(f"\n[INTENTO {attempt}] Enviando solicitud GET...")
            start_time = time.time()
            
            response = requests.get(
                f"{API_URL}{ENDPOINT}",
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                print(f"[OK ✓] Status: {response.status_code} | Tiempo: {elapsed:.2f}s")
                data = response.json()
                print(f"[OK ✓] Inventarios retornados: {data.get('count', 0)}")
                success_count += 1
            else:
                print(f"[ERROR ✗] Status: {response.status_code}")
                print(f"[ERROR ✗] Response: {response.text[:200]}")
                error_count += 1
                
        except requests.exceptions.Timeout:
            print(f"[ERROR ✗] Timeout después de 60 segundos")
            error_count += 1
        except requests.exceptions.ConnectionError:
            print(f"[ERROR ✗] No se puede conectar al servidor")
            print(f"[ERROR ✗] Verifica que NSSM está ejecutando")
            error_count += 1
        except Exception as e:
            print(f"[ERROR ✗] Error inesperado: {str(e)}")
            error_count += 1
        
        # Esperar entre intentos
        if attempt < 5:
            print(f"[TEST] Esperando 3 segundos antes del siguiente intento...")
            time.sleep(3)
    
    # Resumen
    print("\n" + "=" * 80)
    print("[RESULTADO FINAL]")
    print(f"├─ Intentos exitosos: {success_count}/5")
    print(f"├─ Intentos fallidos: {error_count}/5")
    
    if success_count == 5:
        print(f"└─ CONCLUSIÓN: ✓ Servicio ESTABLE (sin reinicio después de solicitudes)")
    elif success_count > 0:
        print(f"└─ CONCLUSIÓN: ⚠ Servicio INESTABLE (se reinicia periódicamente)")
    else:
        print(f"└─ CONCLUSIÓN: ✗ Servicio NO RESPONDE")
    
    print("=" * 80)
    
    return success_count == 5

if __name__ == '__main__':
    try:
        success = test_endpoint()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[CANCELADO] Prueba interrumpida por usuario")
        sys.exit(2)
