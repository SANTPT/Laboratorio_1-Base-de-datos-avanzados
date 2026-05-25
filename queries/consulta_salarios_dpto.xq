(: =========================================================================================
   CONSULTA 2: Informe Salarial Agrupado por Departamento
   
   Descripción: 
   Genera un reporte estadístico de los salarios de los empleados agrupados por
   departamento. Calcula métricas clave como el número total de empleados, 
   salario mínimo, salario máximo, salario promedio y la masa salarial total.
   Filtra los departamentos que no tienen empleados asignados.
   
   Fuentes de datos (Entidades combinadas):
   - /sistema_rh/departamentos/departamento
   - /sistema_rh/empleados/empleado
   
   Orden: Alfabético por el nombre del departamento.
   Salida: Elementos <informe_salarial_departamento> con las estadísticas.
   ========================================================================================= :)

for $dpto in doc("/db/hr/esquemas_hr.xml")/sistema_rh/departamentos/departamento
let $empleados := doc("/db/hr/esquemas_hr.xml")/sistema_rh/empleados/empleado[@ref_departamento = $dpto/@id]
where count($empleados) > 0
let $salarios := for $e in $empleados return xs:decimal($e/salario)
order by $dpto/nombre_departamento
return
<informe_salarial_departamento>
  <departamento_id>{data($dpto/@id)}</departamento_id>
  <nombre>{data($dpto/nombre_departamento)}</nombre>
  <num_empleados>{count($empleados)}</num_empleados>
  <salario_minimo>{min($salarios)}</salario_minimo>
  <salario_maximo>{max($salarios)}</salario_maximo>
  <salario_medio>{avg($salarios)}</salario_medio>
  <masa_salarial>{sum($salarios)}</masa_salarial>
</informe_salarial_departamento>
