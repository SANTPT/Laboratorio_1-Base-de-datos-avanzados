import os
import re
import time
import requests
import random
from flask import Flask, render_template, request, jsonify
from lxml import etree

# Inicialización de la aplicación Flask
app = Flask(__name__)

# Configuración de las rutas del sistema de archivos
# BASE_DIR apunta al directorio raíz del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Carpeta donde se almacena el XML y el esquema XSD
DATA_DIR = os.path.join(BASE_DIR, "data")
# Carpeta de consultas (contiene archivos .xq de XQuery y .xsl de XSLT)
QUERIES_DIR = os.path.join(BASE_DIR, "queries")

# Detección y configuración del procesador Saxon-HE para XQuery local
# Intentamos importar 'saxonche' (Saxon C-HE para Python)
try:
    from saxonche import PySaxonProcessor
    SAXON_AVAILABLE = True
    print("[OK] saxonche importado correctamente. Procesamiento local de XQuery activado.")
except ImportError:
    # Si no está instalado, se deshabilita la opción local y se avisa por consola
    SAXON_AVAILABLE = False
    print("[WARNING] saxonche no está instalado o no es compatible. El procesamiento local de XQuery estará desactivado.")

def get_xslt_files():
    """
    Escanea la carpeta de consultas (queries/) y retorna una lista ordenada
    de archivos con extensión .xsl (hojas de estilo XSLT) disponibles.
    """
    files = []
    if os.path.exists(QUERIES_DIR):
        for f in os.listdir(QUERIES_DIR):
            if f.endswith(".xsl"):
                files.append(f)
    return sorted(files)

def get_xquery_presets():
    """
    Escanea la carpeta de consultas (queries/) en busca de archivos .xq (XQuery).
    Lee su contenido y retorna un diccionario mapeando el nombre del archivo
    al código de la consulta XQuery para que el frontend lo pueda cargar dinámicamente.
    """
    presets = {}
    if os.path.exists(QUERIES_DIR):
        for f in os.listdir(QUERIES_DIR):
            if f.endswith(".xq"):
                path = os.path.join(QUERIES_DIR, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        presets[f] = file.read()
                except Exception as e:
                    print(f"Error al leer XQuery preset {f}: {e}")
    return presets

# Diccionario estático con consultas XPath predefinidas (locales)
# Mapea un nombre descriptivo a la expresión XPath correspondiente.
XPATH_PRESETS = {
    "consulta_1_empleados.xpath": "/sistema_rh/empleados/empleado",
    "consulta_2_departamentos.xpath": "/sistema_rh/departamentos/departamento",
    "consulta_3_ciberseguridad.xpath": "/sistema_rh/empleados/empleado[@ref_departamento='70']",
    "consulta_4_historial.xpath": "/sistema_rh/historiales_laborales/historial_laboral",
    "consulta_5_paises_europa.xpath": "/sistema_rh/regiones/region[@id='1']/paises/pais"
}

@app.route("/")
def index():
    """
    Ruta principal (Dashboard).
    Carga las hojas de estilo XSLT, las consultas preestablecidas de XQuery
    y las de XPath, y renderiza la interfaz principal pasándoles estas opciones.
    Parsea todas las listas de entidades del XML para mostrarlas en los menús dinámicos.
    """
    xslt_files = get_xslt_files()
    xquery_presets = get_xquery_presets()
    
    xml_path = os.path.join(DATA_DIR, "esquemas_hr.xml")
    
    # Listas vacías para los selectores del formulario
    regiones_list = []
    paises_list = []
    ubicaciones_list = []
    trabajos_list = []
    departamentos_list = []
    empleados_list = []
    
    # IDs autoincrementados por defecto sugeridos
    next_emp_id = 101
    next_region_id = 1
    next_ubicacion_id = 1000
    next_dept_id = 10
    
    if os.path.exists(xml_path):
        try:
            tree = etree.parse(xml_path)
            root = tree.getroot()
            
            # Regiones
            for r in root.xpath("//region"):
                regiones_list.append({
                    "id": r.get("id"),
                    "nombre": r.get("nombre_region") or r.get("id")
                })
            if regiones_list:
                next_region_id = max(int(r["id"]) for r in regiones_list if r["id"].isdigit()) + 1
                
            # Países
            for p in root.xpath("//pais"):
                region_elem = p.xpath("./ancestor::region")
                region_id = region_elem[0].get("id") if region_elem else ""
                region_nombre = (region_elem[0].get("nombre_region") or region_id) if region_elem else ""
                paises_list.append({
                    "id": p.get("id"),
                    "nombre": p.get("nombre_pais") or p.get("id"),
                    "region_id": region_id,
                    "region_nombre": region_nombre
                })
                
            # Ubicaciones
            for u in root.xpath("//ubicacion"):
                ubicaciones_list.append({
                    "id": u.get("id"),
                    "nombre": f"{u.findtext('ciudad')} ({u.findtext('direccion_calle')})"
                })
            if ubicaciones_list:
                next_ubicacion_id = max(int(u["id"]) for u in ubicaciones_list if u["id"].isdigit()) + 1
                
            # Trabajos
            for t in root.xpath("//trabajo"):
                trabajos_list.append({
                    "id": t.get("id"),
                    "titulo": t.findtext("titulo_trabajo") or t.get("id")
                })
                
            # Departamentos
            for d in root.xpath("//departamento"):
                departamentos_list.append({
                    "id": d.get("id"),
                    "nombre": d.findtext("nombre_departamento") or d.get("id")
                })
            if departamentos_list:
                next_dept_id = max(int(d["id"]) for d in departamentos_list if d["id"].isdigit()) + 1
                
            # Empleados
            for e in root.xpath("//empleado"):
                empleados_list.append({
                    "id": e.get("id"),
                    "nombre": f"{e.findtext('nombre')} {e.findtext('apellidos')}"
                })
            if empleados_list:
                next_emp_id = max(int(e["id"]) for e in empleados_list if e["id"].isdigit()) + 1
                
            # Historiales Laborales
            historiales_list = []
            for h in root.xpath("//historial_laboral"):
                ref_emp = h.get("ref_empleado")
                f_ini = h.findtext("fecha_inicio") or ""
                emp_node = root.xpath(f"//empleado[@id='{ref_emp}']")
                emp_name = f"{emp_node[0].findtext('nombre')} {emp_node[0].findtext('apellidos')}" if emp_node else ref_emp
                historiales_list.append({
                    "ref_empleado": ref_emp,
                    "fecha_inicio": f_ini,
                    "label": f"{emp_name} ({f_ini})"
                })
                
        except Exception as e:
            print(f"Error al analizar el XML para los dropdowns: {e}")
            
    return render_template(
        "index.html",
        xslt_files=xslt_files,
        xquery_presets=xquery_presets,
        xpath_presets=XPATH_PRESETS,
        saxon_available=SAXON_AVAILABLE,
        regiones_list=regiones_list,
        paises_list=paises_list,
        ubicaciones_list=ubicaciones_list,
        trabajos_list=trabajos_list,
        departamentos_list=departamentos_list,
        empleados_list=empleados_list,
        historiales_list=historiales_list,
        next_emp_id=next_emp_id,
        next_region_id=next_region_id,
        next_ubicacion_id=next_ubicacion_id,
        next_dept_id=next_dept_id
    )

@app.route("/get_preset_content", methods=["GET"])
def get_preset_content():
    """
    Ruta API para recuperar el contenido de texto de una consulta o transformación.
    Parámetros GET:
      - name: Nombre del archivo de consulta.
      - type: Tipo de consulta ("xpath", "xquery" o "xslt").
    """
    name = request.args.get("name")
    ptype = request.args.get("type")
    
    # Si es XPath, devolvemos el valor desde nuestro diccionario estático
    if ptype == "xpath" and name in XPATH_PRESETS:
        return jsonify({"success": True, "content": XPATH_PRESETS[name]})
    # Si es XQuery, leemos los presets dinámicos desde disco
    elif ptype == "xquery":
        presets = get_xquery_presets()
        if name in presets:
            return jsonify({"success": True, "content": presets[name]})
            
    # Si es una hoja de estilo XSLT, buscamos el archivo en la carpeta queries/
    if name:
        path = os.path.join(QUERIES_DIR, name)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    return jsonify({"success": True, "content": file.read()})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)})
                
    return jsonify({"success": False, "error": "Preset no encontrado"})

@app.route("/ejecutar", methods=["POST"])
def ejecutar():
    """
    Ruta API para ejecutar consultas XPath o XQuery sobre el archivo XML.
    Parámetros JSON (POST):
      - xml_file: Archivo XML sobre el que consultar (por defecto 'esquemas_hr.xml').
      - query_type: Tipo de consulta ('xpath' o 'xquery').
      - query_text: Código de la consulta a ejecutar.
      - engine: Motor para XQuery ('local' con Saxon-HE o 'existdb' con servidor REST).
      - exist_url, exist_user, exist_pass: Parámetros de conexión a la base de datos eXist-db.
    """
    xml_file = request.json.get("xml_file") or "esquemas_hr.xml"
    query_type = request.json.get("query_type")
    query_text = request.json.get("query_text")
    engine = request.json.get("engine", "local")
    
    # Credenciales y endpoint de eXist-db
    exist_url = request.json.get("exist_url", "http://localhost:8080/exist/rest/db")
    exist_user = request.json.get("exist_user", "admin")
    exist_pass = request.json.get("exist_pass", "")

    # Ruta absoluta del XML
    xml_path = os.path.join(DATA_DIR, xml_file)
    
    if not os.path.exists(xml_path):
        return jsonify({"success": False, "error": f"El archivo XML '{xml_file}' no existe."})
        
    start_time = time.time()
    
    try:
        if query_type == "xpath":
            # --- Procesamiento de consulta XPath local ---
            # Cargamos el XML usando lxml
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(xml_path, parser)
            
            # Ejecutamos la consulta XPath
            results = tree.xpath(query_text)
            
            # Convertimos cada nodo coincidente en su representación string XML
            output_list = []
            for r in results:
                if isinstance(r, etree._Element):
                    output_list.append(etree.tostring(r, pretty_print=True, encoding='unicode'))
                else:
                    # Si el resultado es un texto o un atributo simple
                    output_list.append(str(r))
            
            elapsed = (time.time() - start_time) * 1000
            result_str = "\n".join(output_list)
            if not result_str:
                result_str = "<!-- No se encontraron resultados que coincidan con la expresión XPath -->"
                
            return jsonify({
                "success": True,
                "result": result_str,
                "count": len(results),
                "elapsed_ms": round(elapsed, 2)
            })
            
        elif query_type == "xquery":
            # --- Procesamiento de consulta XQuery ---
            if engine == "existdb":
                # Método A: Consultar en base de datos nativa eXist-db mediante su API REST
                try:
                    response = requests.post(
                        exist_url,
                        data={"_query": query_text},
                        auth=(exist_user, exist_pass),
                        timeout=5
                    )
                    elapsed = (time.time() - start_time) * 1000
                    if response.status_code == 200:
                        return jsonify({
                            "success": True,
                            "result": response.text,
                            "elapsed_ms": round(elapsed, 2)
                        })
                    else:
                        return jsonify({
                            "success": False,
                            "error": f"Error del servidor eXist-db (Código {response.status_code}):\n{response.text}"
                        })
                except requests.exceptions.RequestException as e:
                    return jsonify({
                        "success": False,
                        "error": f"Error de conexión con eXist-db:\n{str(e)}\n\nAsegúrate de que eXist-db esté corriendo en {exist_url} o cambia al motor local Saxon-HE."
                    })
            else:
                # Método B: Consultar de manera local usando Saxon-HE (saxonche)
                if not SAXON_AVAILABLE:
                    return jsonify({
                        "success": False,
                        "error": "El procesador Saxon-HE no está disponible en este servidor. Por favor, usa eXist-db o XPath."
                    })
                
                # Para Saxon local, debemos resolver la ruta del archivo de forma absoluta
                abs_xml_path = os.path.abspath(xml_path).replace("\\", "/")
                
                # Modificamos las llamadas típicas de eXist-db como doc("/db/hr/archivo.xml")
                # para que apunten a la ruta local del archivo en disco
                modified_query = query_text
                modified_query = modified_query.replace('doc("/db/hr/esquemas_hr.xml")', f'doc("{abs_xml_path}")')
                # Reemplazo general dinámico para cualquier ruta XML bajo /db/hr/
                modified_query = re.sub(
                    r'doc\("/db/hr/([^"]+)"\)',
                    lambda m: f'doc("{os.path.abspath(os.path.join(DATA_DIR, m.group(1))).replace("\\", "/")}")',
                    modified_query
                )
                
                # Inicialización y ejecución con Saxon-HE
                with PySaxonProcessor(license=False) as proc:
                    xq_proc = proc.new_xquery_processor()
                    xq_proc.set_query_content(modified_query)
                    result = xq_proc.run_query_to_string()
                    
                    elapsed = (time.time() - start_time) * 1000
                    return jsonify({
                        "success": True,
                        "result": result,
                        "elapsed_ms": round(elapsed, 2)
                    })
                    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error de ejecución:\n{str(e)}"
        })

@app.route("/validar", methods=["POST"])
def validar():
    """
    Ruta API para validar el archivo XML contra el esquema XSD de Recursos Humanos.
    Parámetros JSON:
      - xml_file: Nombre del archivo a validar (por defecto 'esquemas_hr.xml').
    """
    xml_file = request.json.get("xml_file") or "esquemas_hr.xml"
    xml_path = os.path.join(DATA_DIR, xml_file)
    xsd_path = os.path.join(DATA_DIR, "esquemas_hr.xsd")
    
    if not os.path.exists(xml_path):
        return jsonify({"success": False, "error": f"El archivo XML '{xml_file}' no existe."})
    if not os.path.exists(xsd_path):
        return jsonify({"success": False, "error": "El archivo de esquema XSD 'esquemas_hr.xsd' no existe en data/."})
        
    try:
        # Parseo de los documentos XML y XSD usando lxml
        xml_doc = etree.parse(xml_path)
        xsd_doc = etree.parse(xsd_path)
        # Compilación del validador de esquemas XML
        schema = etree.XMLSchema(xsd_doc)
        
        # Validación del documento XML
        if schema.validate(xml_doc):
            return jsonify({
                "success": True,
                "message": f"El archivo '{xml_file}' es VÁLIDO según el esquema XSD de Recursos Humanos."
            })
        else:
            # En caso de fallo, recopilamos todos los errores con su número de línea y mensaje
            errors = []
            for error in schema.error_log:
                errors.append(f"Línea {error.line}: {error.message}")
            return jsonify({
                "success": False,
                "error": "Errores de validación encontrados:\n" + "\n".join(errors)
            })
            
    except etree.XMLSyntaxError as e:
        return jsonify({"success": False, "error": f"Error de sintaxis XML:\n{str(e)}"})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error general en validación:\n{str(e)}"})

@app.route("/insertar_dato", methods=["POST"])
def insertar_dato():
    """
    Endpoint único para la inserción manual de datos en cualquiera de las 7 tablas/entidades
    del archivo esquemas_hr.xml, realizando validaciones preventivas detalladas conforme al XSD.
    """
    entity = request.json.get("entity")
    data = request.json.get("data", {})
    
    xml_path = os.path.join(DATA_DIR, "esquemas_hr.xml")
    if not os.path.exists(xml_path):
        return jsonify({"success": False, "error": "No se encontró el archivo esquemas_hr.xml."})
        
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()
        
        if entity == "region":
            # --- REGION ---
            reg_id = data.get("id")
            nombre = data.get("nombre_region", "").strip()
            
            if not reg_id or not nombre:
                return jsonify({"success": False, "error": "Todos los campos de la región son obligatorios."})
            if not str(reg_id).isdigit():
                return jsonify({"success": False, "error": "El ID de la región debe ser un número entero."})
                
            regiones_node = root.find("regiones")
            if regiones_node is None:
                return jsonify({"success": False, "error": "No se encontró el nodo <regiones>."})
                
            for r in regiones_node.findall("region"):
                if r.get("id") == str(reg_id):
                    return jsonify({"success": False, "error": f"La región con ID {reg_id} ya existe."})
                    
            reg_elem = etree.SubElement(regiones_node, "region", id=str(reg_id), nombre_region=nombre)
            etree.SubElement(reg_elem, "paises") # Elemento obligatorio dentro de region según XSD
            
        elif entity == "pais":
            # --- PAIS ---
            pais_id = data.get("id", "").strip().upper()
            nombre = data.get("nombre_pais", "").strip()
            ref_region = data.get("ref_region")
            
            if not pais_id or not nombre or not ref_region:
                return jsonify({"success": False, "error": "Todos los campos del país son obligatorios."})
                
            # Validar unicidad del ID de país
            for p in root.xpath("//pais"):
                if p.get("id") == pais_id:
                    return jsonify({"success": False, "error": f"El país con ID '{pais_id}' ya existe."})
                    
            # Encontrar región contenedora
            region_node = root.xpath(f"//region[@id='{ref_region}']")
            if not region_node:
                return jsonify({"success": False, "error": f"La región con ID {ref_region} no existe."})
                
            paises_node = region_node[0].find("paises")
            if paises_node is None:
                paises_node = etree.SubElement(region_node[0], "paises")
                
            etree.SubElement(paises_node, "pais", id=pais_id, nombre_pais=nombre)
            
        elif entity == "ubicacion":
            # --- UBICACION ---
            ub_id = data.get("id")
            calle = data.get("direccion_calle", "").strip()
            cp = data.get("codigo_postal", "").strip()
            ciudad = data.get("ciudad", "").strip()
            provincia = data.get("provincia_estado", "").strip()
            ref_pais = data.get("ref_pais")
            
            if not ub_id or not calle or not cp or not ciudad or not ref_pais:
                return jsonify({"success": False, "error": "ID, Calle, Código Postal, Ciudad y País son obligatorios."})
            if not str(ub_id).isdigit():
                return jsonify({"success": False, "error": "El ID de ubicación debe ser un número entero."})
                
            ubicaciones_node = root.find("ubicaciones")
            if ubicaciones_node is None:
                return jsonify({"success": False, "error": "No se encontró el nodo <ubicaciones>."})
                
            for u in ubicaciones_node.findall("ubicacion"):
                if u.get("id") == str(ub_id):
                    return jsonify({"success": False, "error": f"La ubicación con ID {ub_id} ya existe."})
                    
            ub_elem = etree.SubElement(ubicaciones_node, "ubicacion", id=str(ub_id), ref_pais=str(ref_pais))
            etree.SubElement(ub_elem, "direccion_calle").text = calle
            etree.SubElement(ub_elem, "codigo_postal").text = cp
            etree.SubElement(ub_elem, "ciudad").text = ciudad
            if provincia:
                etree.SubElement(ub_elem, "provincia_estado").text = provincia
                
        elif entity == "trabajo":
            # --- TRABAJO ---
            tr_id = data.get("id", "").strip().upper()
            titulo = data.get("titulo_trabajo", "").strip()
            s_min = data.get("salario_min")
            s_max = data.get("salario_max")
            
            if not tr_id or not titulo or not s_min or not s_max:
                return jsonify({"success": False, "error": "Todos los campos de trabajo son obligatorios."})
                
            trabajos_node = root.find("trabajos")
            if trabajos_node is None:
                return jsonify({"success": False, "error": "No se encontró el nodo <trabajos>."})
                
            for t in trabajos_node.findall("trabajo"):
                if t.get("id") == tr_id:
                    return jsonify({"success": False, "error": f"El trabajo con ID '{tr_id}' ya existe."})
                    
            try:
                float(s_min)
                float(s_max)
            except ValueError:
                return jsonify({"success": False, "error": "Los salarios mínimos y máximos deben ser números decimales."})
                
            tr_elem = etree.SubElement(trabajos_node, "trabajo", id=tr_id)
            etree.SubElement(tr_elem, "titulo_trabajo").text = titulo
            etree.SubElement(tr_elem, "salario_min").text = str(s_min)
            etree.SubElement(tr_elem, "salario_max").text = str(s_max)
            
        elif entity == "departamento":
            # --- DEPARTAMENTO ---
            dept_id = data.get("id")
            nombre = data.get("nombre_departamento", "").strip()
            id_gerente = data.get("id_gerente")
            ref_ubicacion = data.get("ref_ubicacion")
            
            if not dept_id or not nombre or not ref_ubicacion:
                return jsonify({"success": False, "error": "ID, Nombre de departamento y Ubicación son obligatorios."})
            if not str(dept_id).isdigit():
                return jsonify({"success": False, "error": "El ID del departamento debe ser un número entero."})
                
            departamentos_node = root.find("departamentos")
            if departamentos_node is None:
                return jsonify({"success": False, "error": "No se encontró el nodo <departamentos>."})
                
            for d in departamentos_node.findall("departamento"):
                if d.get("id") == str(dept_id):
                    return jsonify({"success": False, "error": f"El departamento con ID {dept_id} ya existe."})
                    
            dept_elem = etree.SubElement(departamentos_node, "departamento", id=str(dept_id), ref_ubicacion=str(ref_ubicacion))
            etree.SubElement(dept_elem, "nombre_departamento").text = nombre
            if id_gerente:
                if not str(id_gerente).isdigit():
                    return jsonify({"success": False, "error": "El ID del gerente debe ser un número entero."})
                etree.SubElement(dept_elem, "id_gerente").text = str(id_gerente)
                
        elif entity == "empleado":
            # --- EMPLEADO ---
            emp_id = data.get("id")
            ref_dpto = data.get("ref_departamento")
            ref_trabajo = data.get("ref_trabajo")
            nombre = data.get("nombre", "").strip()
            apellidos = data.get("apellidos", "").strip()
            email = data.get("email", "").strip().lower()
            telefono = data.get("telefono", "").strip()
            fecha = data.get("fecha_contratacion", "").strip()
            salario = data.get("salario", "").strip()
            comision = data.get("porcentaje_comision", "").strip()
            
            if not all([emp_id, ref_dpto, ref_trabajo, nombre, apellidos, email, telefono, fecha, salario]):
                return jsonify({"success": False, "error": "Todos los campos de empleado son obligatorios."})
            if not str(emp_id).isdigit():
                return jsonify({"success": False, "error": "El ID del empleado debe ser un número entero."})
                
            empleados_node = root.find("empleados")
            if empleados_node is None:
                return jsonify({"success": False, "error": "No se encontró el nodo <empleados>."})
                
            for emp in empleados_node.findall("empleado"):
                if emp.get("id") == str(emp_id):
                    return jsonify({"success": False, "error": f"El ID de empleado '{emp_id}' ya existe."})
                if emp.findtext("email") == email:
                    return jsonify({"success": False, "error": f"El email '{email}' ya pertenece a otro empleado."})
                    
            if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email):
                return jsonify({"success": False, "error": "El email no cumple con la restricción XSD (ejemplo: usuario@correo.com)."})
                
            try:
                float(salario)
            except ValueError:
                return jsonify({"success": False, "error": "El salario debe ser un número decimal."})
                
            if comision:
                try:
                    float(comision)
                except ValueError:
                    return jsonify({"success": False, "error": "El porcentaje de comisión debe ser un número decimal."})
                    
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha):
                return jsonify({"success": False, "error": "La fecha de contratación debe seguir el formato AAAA-MM-DD."})
                
            emp_elem = etree.SubElement(empleados_node, "empleado", id=str(emp_id), ref_departamento=str(ref_dpto), ref_trabajo=str(ref_trabajo))
            etree.SubElement(emp_elem, "nombre").text = nombre
            etree.SubElement(emp_elem, "apellidos").text = apellidos
            etree.SubElement(emp_elem, "email").text = email
            etree.SubElement(emp_elem, "telefono").text = telefono
            etree.SubElement(emp_elem, "fecha_contratacion").text = fecha
            etree.SubElement(emp_elem, "salario").text = str(salario)
            if comision:
                etree.SubElement(emp_elem, "porcentaje_comision").text = str(comision)
                
        elif entity == "historial_laboral":
            # --- HISTORIAL LABORAL ---
            ref_emp = data.get("ref_empleado")
            f_ini = data.get("fecha_inicio", "").strip()
            f_fin = data.get("fecha_fin", "").strip()
            ref_tr = data.get("ref_trabajo")
            ref_dp = data.get("ref_departamento")
            
            if not all([ref_emp, f_ini, f_fin, ref_tr, ref_dp]):
                return jsonify({"success": False, "error": "Todos los campos de historial laboral son obligatorios."})
                
            historiales_node = root.find("historiales_laborales")
            if historiales_node is None:
                historiales_node = etree.SubElement(root, "historiales_laborales")
                
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", f_ini) or not re.match(r"^\d{4}-\d{2}-\d{2}$", f_fin):
                return jsonify({"success": False, "error": "Las fechas de inicio y fin deben seguir el formato AAAA-MM-DD."})
                
            hist_elem = etree.SubElement(historiales_node, "historial_laboral", ref_empleado=str(ref_emp))
            etree.SubElement(hist_elem, "fecha_inicio").text = f_ini
            etree.SubElement(hist_elem, "fecha_fin").text = f_fin
            etree.SubElement(hist_elem, "ref_trabajo").text = str(ref_tr)
            etree.SubElement(hist_elem, "ref_departamento").text = str(ref_dp)
            
        else:
            return jsonify({"success": False, "error": "Entidad o tabla no válida para registro."})
            
        # Escribir de vuelta al XML conservando el formato indentado
        tree.write(xml_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        
        return jsonify({
            "success": True,
            "message": f"Registro insertado con éxito en la tabla '{entity}'."
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al insertar en la base de datos XML: {str(e)}"})


@app.route("/obtener_dato", methods=["GET"])
def obtener_dato():
    """
    Recupera un registro específico de la base de datos XML y devuelve sus datos como JSON.
    """
    entity = request.args.get("entity")
    record_id = request.args.get("id")
    fecha_inicio = request.args.get("fecha_inicio")  # Solo para historial_laboral
    
    xml_path = os.path.join(DATA_DIR, "esquemas_hr.xml")
    if not os.path.exists(xml_path):
        return jsonify({"success": False, "error": "No se encontró el archivo esquemas_hr.xml."})
        
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()
        
        nodes = []
        if entity == "region":
            nodes = root.xpath(f"//region[@id='{record_id}']")
        elif entity == "pais":
            nodes = root.xpath(f"//pais[@id='{record_id}']")
        elif entity == "ubicacion":
            nodes = root.xpath(f"//ubicacion[@id='{record_id}']")
        elif entity == "trabajo":
            nodes = root.xpath(f"//trabajo[@id='{record_id}']")
        elif entity == "departamento":
            nodes = root.xpath(f"//departamento[@id='{record_id}']")
        elif entity == "empleado":
            nodes = root.xpath(f"//empleado[@id='{record_id}']")
        elif entity == "historial_laboral":
            nodes = root.xpath(f"//historial_laboral[@ref_empleado='{record_id}' and fecha_inicio='{fecha_inicio}']")
        else:
            return jsonify({"success": False, "error": "Entidad no válida."})
            
        if not nodes:
            return jsonify({"success": False, "error": "Registro no encontrado."})
            
        node = nodes[0]
        data = {}
        
        # Extraer atributos
        for k, v in node.attrib.items():
            data[k] = v
            
        # Extraer elementos hijo simples (sin hijos internos)
        for child in node:
            if isinstance(child.tag, str) and len(child) == 0:
                data[child.tag] = child.text if child.text is not None else ""
                
        return jsonify({"success": True, "data": data})
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al obtener datos: {str(e)}"})


@app.route("/actualizar_dato", methods=["POST"])
def actualizar_dato():
    """
    Modifica un registro existente en el XML, validándolo previamente con el XSD.
    """
    entity = request.json.get("entity")
    record_id = request.json.get("id")
    fecha_inicio_orig = request.json.get("fecha_inicio_orig")  # Solo para historial_laboral
    data = request.json.get("data", {})
    
    xml_path = os.path.join(DATA_DIR, "esquemas_hr.xml")
    xsd_path = os.path.join(DATA_DIR, "esquemas_hr.xsd")
    
    if not os.path.exists(xml_path):
        return jsonify({"success": False, "error": "No se encontró el archivo esquemas_hr.xml."})
        
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()
        
        nodes = []
        if entity == "region":
            nodes = root.xpath(f"//region[@id='{record_id}']")
        elif entity == "pais":
            nodes = root.xpath(f"//pais[@id='{record_id}']")
        elif entity == "ubicacion":
            nodes = root.xpath(f"//ubicacion[@id='{record_id}']")
        elif entity == "trabajo":
            nodes = root.xpath(f"//trabajo[@id='{record_id}']")
        elif entity == "departamento":
            nodes = root.xpath(f"//departamento[@id='{record_id}']")
        elif entity == "empleado":
            nodes = root.xpath(f"//empleado[@id='{record_id}']")
        elif entity == "historial_laboral":
            nodes = root.xpath(f"//historial_laboral[@ref_empleado='{record_id}' and fecha_inicio='{fecha_inicio_orig}']")
            
        if not nodes:
            return jsonify({"success": False, "error": "Registro a actualizar no encontrado."})
            
        node = nodes[0]
        
        # Validar y actualizar campos según la entidad
        if entity == "region":
            nombre = data.get("nombre_region", "").strip()
            if not nombre:
                return jsonify({"success": False, "error": "El nombre de la región es obligatorio."})
            node.set("nombre_region", nombre)
            
        elif entity == "pais":
            nombre = data.get("nombre_pais", "").strip()
            ref_region = data.get("ref_region")
            if not nombre or not ref_region:
                return jsonify({"success": False, "error": "Todos los campos de país son obligatorios."})
                
            # Verificar existencia de la región
            region_node = root.xpath(f"//region[@id='{ref_region}']")
            if not region_node:
                return jsonify({"success": False, "error": f"La región con ID {ref_region} no existe."})
                
            node.set("nombre_pais", nombre)
            
            # Si cambió la región, mover el nodo <pais> a su nueva región correspondiente
            current_region = node.xpath("./ancestor::region")[0]
            if current_region.get("id") != str(ref_region):
                node.getparent().remove(node)
                paises_node = region_node[0].find("paises")
                if paises_node is None:
                    paises_node = etree.SubElement(region_node[0], "paises")
                paises_node.append(node)
                
        elif entity == "ubicacion":
            calle = data.get("direccion_calle", "").strip()
            cp = data.get("codigo_postal", "").strip()
            ciudad = data.get("ciudad", "").strip()
            provincia = data.get("provincia_estado", "").strip()
            ref_pais = data.get("ref_pais")
            
            if not calle or not cp or not ciudad or not ref_pais:
                return jsonify({"success": False, "error": "Calle, Cód. Postal, Ciudad y País son obligatorios."})
                
            # Verificar país
            if not root.xpath(f"//pais[@id='{ref_pais}']"):
                return jsonify({"success": False, "error": f"El país con ID '{ref_pais}' no existe."})
                
            node.set("ref_pais", str(ref_pais))
            node.find("direccion_calle").text = calle
            node.find("codigo_postal").text = cp
            node.find("ciudad").text = ciudad
            
            prov_elem = node.find("provincia_estado")
            if provincia:
                if prov_elem is None:
                    prov_elem = etree.SubElement(node, "provincia_estado")
                prov_elem.text = provincia
            else:
                if prov_elem is not None:
                    node.remove(prov_elem)
                    
        elif entity == "trabajo":
            titulo = data.get("titulo_trabajo", "").strip()
            s_min = data.get("salario_min")
            s_max = data.get("salario_max")
            
            if not titulo or not s_min or not s_max:
                return jsonify({"success": False, "error": "Todos los campos de trabajo son obligatorios."})
            try:
                float(s_min)
                float(s_max)
            except ValueError:
                return jsonify({"success": False, "error": "Los salarios deben ser números decimales."})
                
            node.find("titulo_trabajo").text = titulo
            node.find("salario_min").text = str(s_min)
            node.find("salario_max").text = str(s_max)
            
        elif entity == "departamento":
            nombre = data.get("nombre_departamento", "").strip()
            id_gerente = data.get("id_gerente")
            ref_ubicacion = data.get("ref_ubicacion")
            
            if not nombre or not ref_ubicacion:
                return jsonify({"success": False, "error": "Nombre de departamento y Ubicación son obligatorios."})
                
            # Verificar ubicación
            if not root.xpath(f"//ubicacion[@id='{ref_ubicacion}']"):
                return jsonify({"success": False, "error": f"La ubicación con ID {ref_ubicacion} no existe."})
                
            node.set("ref_ubicacion", str(ref_ubicacion))
            node.find("nombre_departamento").text = nombre
            
            ger_elem = node.find("id_gerente")
            if id_gerente:
                if not str(id_gerente).isdigit():
                    return jsonify({"success": False, "error": "El ID del gerente debe ser un número entero."})
                if not root.xpath(f"//empleado[@id='{id_gerente}']"):
                    return jsonify({"success": False, "error": f"El gerente con ID {id_gerente} no existe en la lista de empleados."})
                if ger_elem is None:
                    ger_elem = etree.SubElement(node, "id_gerente")
                ger_elem.text = str(id_gerente)
            else:
                if ger_elem is not None:
                    node.remove(ger_elem)
                    
        elif entity == "empleado":
            ref_dpto = data.get("ref_departamento")
            ref_trabajo = data.get("ref_trabajo")
            nombre = data.get("nombre", "").strip()
            apellidos = data.get("apellidos", "").strip()
            email = data.get("email", "").strip().lower()
            telefono = data.get("telefono", "").strip()
            fecha = data.get("fecha_contratacion", "").strip()
            salario = data.get("salario", "").strip()
            comision = data.get("porcentaje_comision", "").strip()
            
            if not all([ref_dpto, ref_trabajo, nombre, apellidos, email, telefono, fecha, salario]):
                return jsonify({"success": False, "error": "Todos los campos de empleado son obligatorios."})
                
            # Verificar email único contra otros empleados
            for emp in root.xpath("//empleado"):
                if emp.get("id") != str(record_id) and emp.findtext("email") == email:
                    return jsonify({"success": False, "error": f"El email '{email}' ya está asignado a otro empleado."})
                    
            if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email):
                return jsonify({"success": False, "error": "El email debe cumplir con el formato estándar (ejemplo: usuario@correo.com)."})
                
            try:
                float(salario)
            except ValueError:
                return jsonify({"success": False, "error": "El salario debe ser un número decimal."})
                
            if comision:
                try:
                    float(comision)
                except ValueError:
                    return jsonify({"success": False, "error": "La comisión debe ser un número decimal."})
                    
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", fecha):
                return jsonify({"success": False, "error": "La fecha debe tener formato AAAA-MM-DD."})
                
            node.set("ref_departamento", str(ref_dpto))
            node.set("ref_trabajo", str(ref_trabajo))
            node.find("nombre").text = nombre
            node.find("apellidos").text = apellidos
            node.find("email").text = email
            node.find("telefono").text = telefono
            node.find("fecha_contratacion").text = fecha
            node.find("salario").text = str(salario)
            
            com_elem = node.find("porcentaje_comision")
            if comision:
                if com_elem is None:
                    com_elem = etree.SubElement(node, "porcentaje_comision")
                com_elem.text = str(comision)
            else:
                if com_elem is not None:
                    node.remove(com_elem)
                    
        elif entity == "historial_laboral":
            ref_emp = data.get("ref_empleado")
            f_ini = data.get("fecha_inicio", "").strip()
            f_fin = data.get("fecha_fin", "").strip()
            ref_tr = data.get("ref_trabajo")
            ref_dp = data.get("ref_departamento")
            
            if not all([ref_emp, f_ini, f_fin, ref_tr, ref_dp]):
                return jsonify({"success": False, "error": "Todos los campos del historial son obligatorios."})
                
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", f_ini) or not re.match(r"^\d{4}-\d{2}-\d{2}$", f_fin):
                return jsonify({"success": False, "error": "Las fechas deben tener formato AAAA-MM-DD."})
                
            # Verificar empleado
            if not root.xpath(f"//empleado[@id='{ref_emp}']"):
                return jsonify({"success": False, "error": f"El empleado {ref_emp} no existe."})
                
            node.set("ref_empleado", str(ref_emp))
            node.find("fecha_inicio").text = f_ini
            node.find("fecha_fin").text = f_fin
            node.find("ref_trabajo").text = str(ref_tr)
            node.find("ref_departamento").text = str(ref_dp)
            
        # Validar el XML resultante contra el XSD antes de guardar
        if os.path.exists(xsd_path):
            try:
                xsd_doc = etree.parse(xsd_path)
                schema = etree.XMLSchema(xsd_doc)
                if not schema.validate(tree):
                    errors = [f"Línea {err.line}: {err.message}" for err in schema.error_log]
                    return jsonify({"success": False, "error": "Los cambios violan el esquema XSD:\n" + "\n".join(errors)})
            except Exception as e_xsd:
                print(f"Error en validación XSD durante actualización: {e_xsd}")
                
        # Escribir cambios
        tree.write(xml_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        return jsonify({"success": True, "message": "Registro actualizado correctamente."})
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al actualizar: {str(e)}"})


@app.route("/eliminar_dato", methods=["POST"])
def eliminar_dato():
    """
    Elimina un registro específico del XML tras validar restricciones de integridad referencial.
    """
    entity = request.json.get("entity")
    record_id = request.json.get("id")
    fecha_inicio = request.json.get("fecha_inicio")  # Solo para historial_laboral
    
    xml_path = os.path.join(DATA_DIR, "esquemas_hr.xml")
    xsd_path = os.path.join(DATA_DIR, "esquemas_hr.xsd")
    
    if not os.path.exists(xml_path):
        return jsonify({"success": False, "error": "No se encontró el archivo esquemas_hr.xml."})
        
    try:
        tree = etree.parse(xml_path)
        root = tree.getroot()
        
        nodes = []
        if entity == "region":
            nodes = root.xpath(f"//region[@id='{record_id}']")
        elif entity == "pais":
            nodes = root.xpath(f"//pais[@id='{record_id}']")
        elif entity == "ubicacion":
            nodes = root.xpath(f"//ubicacion[@id='{record_id}']")
        elif entity == "trabajo":
            nodes = root.xpath(f"//trabajo[@id='{record_id}']")
        elif entity == "departamento":
            nodes = root.xpath(f"//departamento[@id='{record_id}']")
        elif entity == "empleado":
            nodes = root.xpath(f"//empleado[@id='{record_id}']")
        elif entity == "historial_laboral":
            nodes = root.xpath(f"//historial_laboral[@ref_empleado='{record_id}' and fecha_inicio='{fecha_inicio}']")
            
        if not nodes:
            return jsonify({"success": False, "error": "Registro a eliminar no encontrado."})
            
        node = nodes[0]
        
        # Validar Integridad Referencial Manualmente (para dar mejores mensajes de error que el validador XSD)
        if entity == "region":
            paises = node.xpath(".//pais")
            if paises:
                return jsonify({"success": False, "error": f"No se puede eliminar la región porque contiene {len(paises)} países asociados. Elimínalos primero."})
        elif entity == "pais":
            ubicaciones = root.xpath(f"//ubicacion[@ref_pais='{record_id}']")
            if ubicaciones:
                return jsonify({"success": False, "error": f"No se puede eliminar el país porque tiene {len(ubicaciones)} ubicaciones asociadas."})
        elif entity == "ubicacion":
            deptos = root.xpath(f"//departamento[@ref_ubicacion='{record_id}']")
            if deptos:
                return jsonify({"success": False, "error": f"No se puede eliminar la ubicación porque tiene {len(deptos)} departamentos asociados."})
        elif entity == "trabajo":
            empleados = root.xpath(f"//empleado[@ref_trabajo='{record_id}']")
            historiales = root.xpath(f"//historial_laboral[ref_trabajo='{record_id}']")
            if empleados or historiales:
                return jsonify({"success": False, "error": "No se puede eliminar el trabajo porque está asignado a empleados u hojas de historial laboral."})
        elif entity == "departamento":
            empleados = root.xpath(f"//empleado[@ref_departamento='{record_id}']")
            historiales = root.xpath(f"//historial_laboral[ref_departamento='{record_id}']")
            if empleados or historiales:
                return jsonify({"success": False, "error": "No se puede eliminar el departamento porque tiene empleados o historiales vinculados."})
        elif entity == "empleado":
            gerente_de = root.xpath(f"//departamento[id_gerente='{record_id}']")
            if gerente_de:
                return jsonify({"success": False, "error": f"No se puede eliminar al empleado porque es gerente del departamento '{gerente_de[0].findtext('nombre_departamento')}'."})
            historiales = root.xpath(f"//historial_laboral[@ref_empleado='{record_id}']")
            if historiales:
                return jsonify({"success": False, "error": f"No se puede eliminar al empleado porque tiene {len(historiales)} registros de historial laboral. Elimina el historial primero."})
                
        # Remover nodo
        node.getparent().remove(node)
        
        # Validar el XML resultante contra el XSD antes de guardar
        if os.path.exists(xsd_path):
            try:
                xsd_doc = etree.parse(xsd_path)
                schema = etree.XMLSchema(xsd_doc)
                if not schema.validate(tree):
                    errors = [f"Línea {err.line}: {err.message}" for err in schema.error_log]
                    return jsonify({"success": False, "error": "La eliminación viola restricciones del esquema XSD:\n" + "\n".join(errors)})
            except Exception as e_xsd:
                print(f"Error en validación XSD durante eliminación: {e_xsd}")
                
        # Guardar
        tree.write(xml_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        return jsonify({"success": True, "message": "Registro eliminado con éxito."})
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al eliminar: {str(e)}"})


@app.route("/obtener_xml_completo", methods=["GET"])
def obtener_xml_completo():
    """
    Lee y devuelve el archivo XML completo de la base de datos para mostrarlo en el Dashboard.
    """
    xml_path = os.path.join(DATA_DIR, "esquemas_hr.xml")
    if not os.path.exists(xml_path):
        return jsonify({"success": False, "error": "No se encontró el archivo esquemas_hr.xml."})
    try:
        with open(xml_path, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"success": True, "content": content})
    except Exception as e:
        return jsonify({"success": False, "error": f"Error al leer el XML completo: {str(e)}"})


@app.route("/transformar", methods=["POST"])
def transformar():
    """
    Aplica una hoja de estilos XSLT sobre los datos XML resultantes de una consulta.
    Evita fugas de estilos (style leaks) a la UI principal del Dashboard eliminando
    etiquetas <style> e inyectando solo el fragmento <table> o el contenido del <body>.
    """
    xml_data = request.json.get("xml_data")
    xslt_file = request.json.get("xslt_file")
    xslt_custom = request.json.get("xslt_custom")
    
    if not xml_data:
        return jsonify({"success": False, "error": "No hay datos XML sobre los cuales aplicar la transformación."})
        
    try:
        # Obtenemos la hoja de estilos personalizada o el archivo seleccionado de la lista
        if xslt_custom:
            xslt_content = xslt_custom
        else:
            xslt_path = os.path.join(QUERIES_DIR, xslt_file)
            if not os.path.exists(xslt_path):
                return jsonify({"success": False, "error": f"El archivo XSLT '{xslt_file}' no existe."})
            with open(xslt_path, 'r', encoding='utf-8') as f:
                xslt_content = f.read()
                
        # Aseguramos que el fragmento XML tenga un único elemento raíz
        xml_data = xml_data.strip()
        
        # Removemos declaraciones XML como <?xml ...?> en el fragmento interno para evitar errores de parseo
        xml_decl = ""
        decl_match = re.match(r'^<\?xml[^>]*\?>', xml_data)
        if decl_match:
            xml_decl = decl_match.group(0)
            xml_data = xml_data[len(xml_decl):].strip()
            
        # Envolvemos el resultado en una etiqueta raíz <resultado>
        wrapped_xml = f"<resultado>{xml_data}</resultado>"
        try:
            xml_doc = etree.fromstring(wrapped_xml.encode('utf-8'))
        except Exception:
            # En caso de error, intentamos procesar la declaración original sin envolver
            xml_doc = etree.fromstring((xml_decl + xml_data).encode('utf-8'))
            
        # Cargamos el XSLT
        xslt_doc = etree.fromstring(xslt_content.encode('utf-8'))
        transform = etree.XSLT(xslt_doc)
        
        # Realizamos la transformación XSLT
        result_tree = transform(xml_doc)
        result_str = str(result_tree)
        
        # --- Limpieza de seguridad de estilos HTML ---
        try:
            html_parser = etree.HTMLParser()
            html_tree = etree.fromstring(result_str.encode('utf-8'), html_parser)
            
            # Eliminamos cualquier bloque <style> dentro del resultado para no alterar la UI del dashboard
            for style in html_tree.xpath("//style"):
                style.getparent().remove(style)
                
            # Extraemos la tabla formateada en XSLT si existe
            table_elem = html_tree.find(".//table")
            if table_elem is not None:
                result_html = etree.tostring(table_elem, pretty_print=True, encoding='unicode')
            else:
                # Si no hay tabla, devolvemos el contenido dentro de <body>
                body_elem = html_tree.find(".//body")
                if body_elem is not None:
                    result_html = "".join([etree.tostring(child, pretty_print=True, encoding='unicode') for child in body_elem])
                else:
                    result_html = result_str
        except Exception as parse_err:
            print(f"Error parsing XSLT HTML output, returning raw output: {parse_err}")
            result_html = result_str
            
        return jsonify({
            "success": True,
            "result": result_html
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Error en la transformación XSLT:\n{str(e)}"})

# Inicializador de la aplicación
if __name__ == "__main__":
    # Arranca el servidor local Flask en el puerto 5000 (o en el especificado por la variable PORT)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
