"""
Consultas XPath sobre el esquema HR con soporte CLI
Asignatura: Bases de Datos Avanzada
"""
from lxml import etree
import argparse
import sys

def ejecutar_consulta_1(tree):
    print("=" * 55)
    print("CONSULTA 1: Empleados con su departamento y puesto")
    print("  XPath: /sistema_rh/empleados/empleado")
    print("=" * 55)
    for emp in tree.xpath("/sistema_rh/empleados/empleado"):
        eid       = emp.get("id")
        nombre    = emp.findtext("nombre")
        apellidos = emp.findtext("apellidos")
        dpto      = emp.get("ref_departamento")
        trabajo   = emp.get("ref_trabajo")
        salario   = emp.findtext("salario")
        print(f"  ID {eid:>4} | {nombre} {apellidos:<25} | Dpto:{dpto:>4} | {trabajo:<12} | €{salario}")

def ejecutar_consulta_2(tree):
    print("=" * 55)
    print("CONSULTA 2: Departamentos y su ubicación")
    print("  XPath: /sistema_rh/departamentos/departamento")
    print("=" * 55)
    for d in tree.xpath("/sistema_rh/departamentos/departamento"):
        print(f"  Dpto {d.get('id'):>4} | Ubic:{d.get('ref_ubicacion'):>5} | {d.findtext('nombre_departamento')}")

def ejecutar_consulta_3(tree):
    print("=" * 55)
    print("CONSULTA 3: Empleados del dpto. Ciberseguridad (70)")
    print("  XPath: /sistema_rh/empleados/empleado[@ref_departamento='70']")
    print("=" * 55)
    for emp in tree.xpath("/sistema_rh/empleados/empleado[@ref_departamento='70']"):
        print(f"  {emp.findtext('nombre')} {emp.findtext('apellidos')} - {emp.get('ref_trabajo')}")

def ejecutar_consulta_4(tree):
    print("=" * 55)
    print("CONSULTA 4: Historial laboral (multi-tabla: empleados + historial)")
    print("  XPath: unión de empleados e historiales_laborales")
    print("=" * 55)
    for h in tree.xpath("/sistema_rh/historiales_laborales/historial_laboral"):
        ref_emp = h.get("ref_empleado")
        emp = tree.xpath(f"/sistema_rh/empleados/empleado[@id='{ref_emp}']")
        nombre_emp = f"{emp[0].findtext('nombre')} {emp[0].findtext('apellidos')}" if emp else "Desconocido"
        print(f"  Empleado {ref_emp} ({nombre_emp}) | {h.findtext('fecha_inicio')} → {h.findtext('fecha_fin')} | Dpto:{h.findtext('ref_departamento')} | Trabajo:{h.findtext('ref_trabajo')}")

def ejecutar_consulta_5(tree):
    print("=" * 55)
    print("CONSULTA 5: Países de la región Europa")
    print("  XPath: /sistema_rh/regiones/region[@id='1']/paises/pais")
    print("=" * 55)
    for p in tree.xpath("/sistema_rh/regiones/region[@id='1']/paises/pais"):
        print(f"  {p.get('id')} - {p.get('nombre_pais')}")

def principal():
    parser = argparse.ArgumentParser(description="Ejecutar consultas XPath sobre HR XML")
    parser.add_argument("--consulta", type=int, choices=[1, 2, 3, 4, 5], help="Número de consulta a ejecutar (1-5)")
    parser.add_argument("--todas", action="store_true", help="Ejecutar todas las consultas")
    parser.add_argument("--archivo", default="data/esquemas_hr.xml", help="Ruta al archivo XML")
    
    args = parser.parse_args()
    
    if not args.consulta and not args.todas:
        parser.print_help()
        sys.exit(1)
        
    try:
        tree = etree.parse(args.archivo)
    except Exception as e:
        print(f"❌ Error al cargar el archivo XML: {e}")
        sys.exit(1)
        
    if args.todas:
        ejecutar_consulta_1(tree)
        print()
        ejecutar_consulta_2(tree)
        print()
        ejecutar_consulta_3(tree)
        print()
        ejecutar_consulta_4(tree)
        print()
        ejecutar_consulta_5(tree)
    else:
        if args.consulta == 1:
            ejecutar_consulta_1(tree)
        elif args.consulta == 2:
            ejecutar_consulta_2(tree)
        elif args.consulta == 3:
            ejecutar_consulta_3(tree)
        elif args.consulta == 4:
            ejecutar_consulta_4(tree)
        elif args.consulta == 5:
            ejecutar_consulta_5(tree)

if __name__ == "__main__":
    principal()
