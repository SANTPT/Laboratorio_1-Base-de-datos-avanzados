"""
Script de validación XML contra esquema XSD
Asignatura: Bases de Datos Avanzada - Esquema HR
"""
from lxml import etree
import sys

def validar(xml_path, xsd_path):
    try:
        xml_doc = etree.parse(xml_path)
        xsd_doc = etree.parse(xsd_path)
        schema = etree.XMLSchema(xsd_doc)

        if schema.validate(xml_doc):
            print(f"✅ '{xml_path}' es VÁLIDO según el esquema XSD.")
        else:
            print(f"❌ '{xml_path}' NO es válido. Errores encontrados:")
            for error in schema.error_log:
                print(f"   Línea {error.line}: {error.message}")

    except etree.XMLSyntaxError as e:
        print(f"❌ Error de sintaxis XML:\n   {e}")
    except Exception as e:
        print(f"❌ Error general:\n   {e}")

if __name__ == "__main__":
    xml = sys.argv[1] if len(sys.argv) > 1 else "data/esquemas_hr.xml"
    xsd = sys.argv[2] if len(sys.argv) > 2 else "data/esquemas_hr.xsd"
    validar(xml, xsd)
