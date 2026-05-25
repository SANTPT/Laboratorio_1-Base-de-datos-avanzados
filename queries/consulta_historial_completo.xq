(: =========================================================================================
   CONSULTA 3: Historial Laboral Enriquecido de Empleados
   
   Descripción: 
   Reconstruye el historial de los cargos que han ocupado los empleados en el pasado.
   Combina múltiples entidades para mostrar no solo las fechas de inicio y fin, sino
   también información contextual como el nombre del empleado, el cargo ocupado, 
   el departamento, la ciudad de ubicación y calcula la duración total en días 
   del periodo laborado.
   
   Fuentes de datos (Entidades combinadas):
   - /sistema_rh/historiales_laborales/historial_laboral
   - /sistema_rh/empleados/empleado
   - /sistema_rh/departamentos/departamento
   - /sistema_rh/ubicaciones/ubicacion
   - /sistema_rh/trabajos/trabajo
   
   Orden: Cronológico según la fecha de inicio del cargo en el historial.
   Salida: Elementos <historial_completo> con los datos expandidos y calculados.
   ========================================================================================= :)

for $h in doc("/db/hr/esquemas_hr.xml")/sistema_rh/historiales_laborales/historial_laboral
let $emp  := doc("/db/hr/esquemas_hr.xml")/sistema_rh/empleados/empleado[@id = $h/@ref_empleado]
let $dpto := doc("/db/hr/esquemas_hr.xml")/sistema_rh/departamentos/departamento[@id = $h/ref_departamento]
let $ubic := doc("/db/hr/esquemas_hr.xml")/sistema_rh/ubicaciones/ubicacion[@id = $dpto/@ref_ubicacion]
let $trab := doc("/db/hr/esquemas_hr.xml")/sistema_rh/trabajos/trabajo[@id = $h/ref_trabajo]
let $dias := days-from-duration(
               xs:date($h/fecha_fin) - xs:date($h/fecha_inicio)
             )
order by $h/fecha_inicio
return
<historial_completo>
  <empleado_id>{data($h/@ref_empleado)}</empleado_id>
  <nombre_empleado>{data($emp/nombre)} {data($emp/apellidos)}</nombre_empleado>
  <puesto_anterior>{data($trab/titulo_trabajo)}</puesto_anterior>
  <departamento_anterior>{data($dpto/nombre_departamento)}</departamento_anterior>
  <ciudad>{data($ubic/ciudad)}</ciudad>
  <fecha_inicio>{data($h/fecha_inicio)}</fecha_inicio>
  <fecha_fin>{data($h/fecha_fin)}</fecha_fin>
  <duracion_dias>{$dias}</duracion_dias>
</historial_completo>
