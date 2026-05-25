"""
Script para ejecutar consultas XQuery directamente en eXist-db usando su API REST.
"""
import requests
import argparse
import sys

def ejecutar_xquery(ruta_archivo, url="http://localhost:8080/exist/rest/db", usuario="admin", password=""):
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            query = f.read()
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{ruta_archivo}'")
        sys.exit(1)

    print(f"🚀 Ejecutando {ruta_archivo} en {url} ...\n")
    
    try:
        response = requests.post(
            url,
            data={"_query": query},
            auth=(usuario, password)
        )
        
        if response.status_code == 200:
            print(response.text)
        else:
            print(f"❌ Error del servidor ({response.status_code}):\n{response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión: No se pudo conectar a eXist-db.")
        print("   Asegúrate de que eXist-db esté corriendo en http://localhost:8080")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecutar un archivo XQuery en eXist-db")
    parser.add_argument("archivo", help="Ruta al archivo .xq")
    parser.add_argument("--url", default="http://localhost:8080/exist/rest/db", help="URL base de eXist-db")
    parser.add_argument("--user", default="admin", help="Usuario de eXist-db")
    parser.add_argument("--password", default="", help="Contraseña de eXist-db")
    
    args = parser.parse_args()
    ejecutar_xquery(args.archivo, args.url, args.user, args.password)
