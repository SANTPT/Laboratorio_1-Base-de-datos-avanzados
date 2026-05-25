(: =========================================================================================
   CONSULTA 1: Detalle de Empleados con Departamento y Puesto
   
   Descripción: 
   Esta consulta extrae información detallada de cada empleado, incluyendo 
   su nombre completo, correo electrónico, salario y fecha de contratación.
   Además, cruza los datos con las colecciones de departamentos y trabajos 
   para obtener el nombre del departamento y el título del puesto que ocupa.
   
   Fuentes de datos (Entidades combinadas): 
   - /sistema_rh/empleados/empleado
   - /sistema_rh/departamentos/departamento
   - /sistema_rh/trabajos/trabajo
   
   Orden: Alfabético por los apellidos del empleado.
   Salida: Elementos <empleado_detalle> con la información consolidada.
   ========================================================================================= :)

for $emp in doc("/db/hr/esquemas_hr.xml")/sistema_rh/empleados/empleado
let $dpto := doc("/db/hr/esquemas_hr.xml")/sistema_rh/departamentos/departamento[@id = $emp/@ref_departamento]
let $trabajo := doc("/db/hr/esquemas_hr.xml")/sistema_rh/trabajos/trabajo[@id = $emp/@ref_trabajo]
order by $emp/apellidos
return
<empleado_detalle>
  <id>{data($emp/@id)}</id>
  <nombre_completo>{data($emp/nombre)} {data($emp/apellidos)}</nombre_completo>
  <email>{data($emp/email)}</email>
  <departamento>{data($dpto/nombre_departamento)}</departamento>
  <puesto>{data($trabajo/titulo_trabajo)}</puesto>
  <salario>{data($emp/salario)}</salario>
  <fecha_contratacion>{data($emp/fecha_contratacion)}</fecha_contratacion>
</empleado_detalle>
