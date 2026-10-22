---
name: comisiones-farmacia-vip
description: >-
  Opera los incentivos de Farmacia VIP (farmaciasvip.lifterdo.com, alias
  farmacia-vip, base farmaciasvip): módulo comisiones_zempac y
  comisiones_formularios. Usar cuando pidan revisar un cálculo de comisiones,
  un CAL-, ventas que no salen en Lifter, un facturador de Zempac, metas,
  encargados, sub-encargados o el modo «Halar ambos».
---

# Comisiones Farmacia VIP (Zempac)

Odoo 14. Alias SSH `farmacia-vip`. URL `farmaciasvip.lifterdo.com`. Base `farmaciasvip`. Conexión: skill `ssh-servidores`.

| | |
|---|---|
| Alias | `farmacia-vip` |
| Usuario SSH | `ubuntu` |
| Servicio | `odoo-server`, usuario de sistema `odoo` |
| Conf | `/etc/odoo-server.conf` |
| Addons | `/odoo/custom/addons/addonsCE14` |
| Módulo de cálculo | `comisiones_zempac` (app **Incentivos Zempac**) |
| Cuestionarios | `comisiones_formularios` (depende del anterior; suma o resta puntos, no trae ventas) |
| Repo del código | `kvillar93/addonsCE14`, rama `master` |

Local:

```powershell
ssh -o BatchMode=yes farmacia-vip "whoami && hostname"
```

SQL y el shell de Odoo van por stdin. En PowerShell, here-string simple `@'...'@`. No armes `ssh ... "psql -c \"SELECT ...\""`.

No reinicies Odoo ni hagas `git pull` en el servidor salvo que **este chat** lo pida. Un enlace de facturador o un «Calcular» reescribe montos de incentivo: no lo ejecutes sin que lo pidan.

El `origin` de ese clone tiene una credencial embebida en la URL. No la imprimas. Si hay que tocar git en el servidor, usa `sudo git -C /odoo/custom/addons/addonsCE14` y no pegues `git remote -v` en el chat.

## Qué mira cada pantalla

Menú **Incentivos Zempac**:

| Menú | Modelo | Para qué |
|---|---|---|
| Cálculos: Sucursales | `comision.calculo` | Hoja mensual por departamento. Nombre `CAL-00xxx` |
| Consultas Zempac → Facturadores | `zempacconsulta.facturadores` | Catálogo que viene de `Vtas_Facturador` |
| Consultas Zempac → Ventas por Sucursal | `zempacconsulta.ventas.sucursal` | Ventas diarias por facturador |
| Consultas Zempac → Sucursales | `zempacconsulta.sucursales` | Sucursal Zempac ligada a un `hr.department` |
| Metas → Cuotas de Facturadores | `comision.meta.cuota.facturador` | Meta que cae en la línea del empleado |
| Metas → Cuotas por Sucursal | `comision.meta.cuota.sucursal` | Meta del resumen «Total Meta Sucursal» |

Estados de la hoja: `borrador`, `en_proceso`, `finalizado`, `cancelado`. El cron «Finalizar mes anterior el día 5» cierra el mes previo. `action_calcular` pone la hoja en `en_proceso` y recalcula todo el departamento.

## Dos pasos distintos

No los mezcles cuando digan «no está halando».

1. **Halar empleados** (`action_actualizar_empleados`). Borra las líneas y vuelve a crearlas según el puesto y `hr.department.modo_carga_empleados`. No trae ventas.
2. **Calcular** (`action_calcular`). Primero corre la consulta **Facturadores** (`comision.consulta.config` tipo `facturadores`, hoy id 3) una sola vez en la petición y vuelve a ligar empleados por cédula exacta. Después, por cada hoja, `_calcular_hoja` suma `total_venta_neta` de los facturadores ya ligados, entre `fecha_inicio` y `fecha_fin`. No filtra por sucursal en la línea de la persona.

El cron diario (`_ejecutar_actualizacion_diaria` y la creación mensual) llama `_calcular_hoja` y no refresca facturadores. «Calcular Masivamente» sigue en bucle, pero la marca en `env.all` hace que la consulta a Zempac salga una vez por clic.

Un empleado puede estar en la hoja con ventas 0. Eso significa que el paso 1 sí corrió y el paso 2 no le encontró facturador ligado.

### Quién entra en la hoja

`hr.employee._es_elegible_comision_periodo`: activo, `approval_state = approved` si el campo existe, y contrato `open` o `close` que solape el período.

`hr.job` decide la sección:

| Campo del puesto | Efecto |
|---|---|
| `tipo_calculo = dependientes_lideres` | Sección Dependientes y Líderes |
| `es_encargado` o `es_sub_encargado` | Sección Encargados y Sub-encargados |

`modo_carga_empleados` del departamento:

| Modo | Dependientes y Líderes | Encargados |
|---|---|---|
| `normal` | Solo `tipo_calculo` de la hoja | Encargados y sub-encargados |
| `halar_ambos` | Dependientes, líderes, encargados y sub-encargados | Solo `es_encargado` / `es_sub_encargado` |
| `solo_dependientes` | Los cuatro perfiles | Nadie |
| `todos_menos_encargados_dep` | Como halar ambos, sin `es_encargado` | Igual que normal |

VIP-19 (CRISTO REY) está en `halar_ambos`. Un sub-encargado sale en las dos secciones. Sus ventas de persona se calculan en Dependientes; el incentivo de encargado usa la nota de la sucursal, no su venta individual.

## Cómo se ata una venta a una persona

```text
Vtas_Facturador.NIR          → zempacconsulta.facturadores.facturador_id
Vtas_Facturador.Cedula       → zempacconsulta.facturadores.cedula   (tal cual, con guiones si Zempac los tiene)
cédula == identification_id
  o passport_id (igualdad exacta) → facturadores.employee_id
ventas.sucursal.facturador_id → facturador_m2o_id
línea del CAL                → suma total_venta_neta de esos facturadores
```

`_sincronizar_empleados` corre al importar facturadores. Si `employee_id` ya tiene valor, no lo pisa. Compara el string completo: `001-1886637-5` no es igual a `00118866375`.

El total de la sucursal (`_compute_resumen_sucursal`) no usa ese enlace. Suma el campo `total` de `zempacconsulta.ventas.sucursal` de las sucursales cuyo `department_id` es el de la hoja. Por eso el total del CAL puede cuadrar con el listado de Zempac y la línea de la persona quedar en 0: sus ventas están en el total y no tienen empleado.

El monto del incentivo a repartir (`_calcular_incentivos`) sí excluye:

- facturador con `grupo` = `CALL CENTER`, si la hoja no es call center
- facturador cuyo empleado está en un departamento con `excluir_ventas_incentivo`

## Checklist: ventas en cero o «no hala»

Hazlo en este orden. Para en el primer eslabón roto.

1. Hoja: `comision_calculo` (`name`, `department_id`, `fecha_inicio`, `fecha_fin`, `state`).
2. Empleado: `hr_employee` activo, `approval_state`, `identification_id`, `passport_id`, `department_id`, `job_id`.
3. Línea: `comision_calculo_linea` con `tipo_tab = 'sucursal'`. Si no hay fila, el problema es el halado de empleados (puesto, modo del departamento, contrato, aprobación). Si hay fila y `ventas_netas = 0`, el problema es el facturador.
4. Facturador: `zempacconsulta_facturadores` por `facturador_id` (NIR de Zempac), nombre o cédula. Revisa `employee_id`, `cedula`, `activo`, `sucursal_id`.
5. Compara cédulas **solo con dígitos**. Si los dígitos coinciden y `employee_id` está vacío, es el fallo de los guiones.
6. Ventas: `zempacconsulta_ventas_sucursal` del `facturador_m2o_id` en el rango de la hoja. Si aquí hay monto y la línea está en 0, falta el `employee_id` del facturador (o el CAL no se ha recalculado después de ligarlo).
7. Si no hay filas de venta para ese `facturador_id`, la consulta API no trajo esos días o el `facturador_m2o_id` quedó vacío porque el facturador no existía cuando se importó la venta.

```powershell
$sql = @'
SELECT c.id, c.name, c.fecha_inicio, c.fecha_fin, c.state, c.department_id, d.name
FROM comision_calculo c
JOIN hr_department d ON d.id = c.department_id
WHERE c.name = 'CAL-00545';
'@
$sql | ssh -o BatchMode=yes farmacia-vip "sudo -u postgres psql -d farmaciasvip"
```

Facturador contra empleado, ignorando guiones y espacios:

```sql
SELECT f.id, f.facturador_id, f.facturador, f.cedula, f.employee_id, f.activo,
       e.id AS emp_id, e.name, e.identification_id
FROM zempacconsulta_facturadores f
LEFT JOIN hr_employee e ON e.active AND (
  regexp_replace(COALESCE(e.identification_id,''), '[^0-9]', '', 'g')
    = regexp_replace(COALESCE(f.cedula,''), '[^0-9]', '', 'g')
  OR regexp_replace(COALESCE(e.passport_id,''), '[^0-9]', '', 'g')
    = regexp_replace(COALESCE(f.cedula,''), '[^0-9]', '', 'g')
)
WHERE f.facturador_id = '1582';
```

Ventas del facturador Odoo en el mes de la hoja:

```sql
SELECT ROUND(SUM(total_venta_neta)::numeric, 2) AS neta,
       ROUND(SUM(total)::numeric, 2) AS total,
       COUNT(*), MIN(fecha), MAX(fecha)
FROM zempacconsulta_ventas_sucursal
WHERE facturador_m2o_id = 982
  AND fecha >= '2026-10-01' AND fecha <= '2026-10-31';
```

Activos sin `employee_id` cuya cédula, ya sin símbolos, pega con un empleado:

```sql
SELECT f.facturador_id, f.facturador, f.cedula, f.sucursal_id,
       e.id AS emp_id, e.name, e.identification_id, e.department_id
FROM zempacconsulta_facturadores f
JOIN hr_employee e ON e.active AND (
  regexp_replace(COALESCE(e.identification_id,''), '[^0-9]', '', 'g')
    = regexp_replace(f.cedula, '[^0-9]', '', 'g')
  OR regexp_replace(COALESCE(e.passport_id,''), '[^0-9]', '', 'g')
    = regexp_replace(f.cedula, '[^0-9]', '', 'g')
)
WHERE f.activo AND f.employee_id IS NULL
  AND regexp_replace(COALESCE(f.cedula,''), '[^0-9]', '', 'g') <> '';
```

## Caso CAL-00545 (22 oct 2026)

JUANA IRIS GONZALEZ RODRIGUEZ, empleado `7887`, cédula `00118866375`, departamento `243` VIP-19 (CRISTO REY), puesto `766` SUB ENCARGADO (`es_sub_encargado`, `tipo_calculo = encargados_subencargados`). Aprobada y activa. La hoja `545` (1–31 oct 2026) ya la tenía en sucursal, canjes, incentivos y encargados. La meta de línea es `355000`.

El facturador Zempac NIR `1582` (`zempacconsulta.facturadores` id `982`) llegó con cédula `001-1886637-5` y sin empleado. El 22 oct 2026, 5:32 p. m. (Santo Domingo), `action_calcular` sobre el CAL-00545 releyó Zempac: la cédula quedó `00118866375`, el empleado `7887` y `ventas_netas` **260,309.02** (30 puntos).

Antes de ese cálculo el total de sucursal del CAL, **664,755.03**, ya cuadraba con el listado de Zempac: las ventas estaban en el total y no en su línea.

Ana María Cordero (`880`, cédula sin guiones, empleado `5843`) y Caroline Milagros Pronk (`1513`, empleado `7729`) sí ligan y sus ventas de línea cuadran.

Al 22 oct 2026 el mismo patrón (activo, sin `employee_id`, dígitos iguales a un empleado) también estaba en:

| NIR | Facturador | Empleado |
|---|---|---|
| 1580 | GENESIS ELIZABETH OLMOS MEJIA | 7881 |
| 1616 | JOHANNA CRISTINA ORTEGA SOSA | 7980 |
| 1582 | JUANA IRIS GONZALEZ RODRIGUEZ | 7887 |
| 1094 | TORALYS MENDEZ PERALTA | 8025 |
| 1007 | YAMEL REGALADO VALDEZ | 4005 |

Vuelve a correr el SQL. No asumas que siguen sin ligar.

## Trampa del campo Sucursal del departamento

`hr.department.sucursal_id` de VIP-19 (id 243) vale `21`. En Zempac, `21` es PADRE CASTELLANO II (`zempacconsulta.sucursales` id 21, departamento 509). Cristo Rey es la sucursal `19`, y ese registro ya tiene `department_id = 243`.

El CAL usa `zempacconsulta.sucursales.department_id`, no el char del departamento. Cambiar el 21 del formulario no mueve las ventas de Juana. El import de sucursales solo rellena `department_id` al **crear** una sucursal nueva (`_procesar_sucursales`); no reescribe las que ya existen.

## Si piden corregirlo

Con la cédula ya igual en Zempac, el botón **Calcular** refresca facturadores y rellena la línea. Reescribe incentivos de todo el departamento.

`_sincronizar_empleados` sigue comparando la cédula carácter por carácter y no pisa un `employee_id` ya puesto. Un guion en Zempac deja el facturador sin empleado hasta el próximo Calcular, después de quitarlo.

El `master` de este servidor iba atrás de GitHub (22 oct 2026: unos 418 commits, ninguno en `comisiones_zempac`). El arreglo está en `master` de `addonsCE14` (`966a5f494`) y en el servidor se aplicó con cherry-pick (`444525c51`), sin traer el resto de `master`. Un `git pull` aquí mezclaría esos cientos de commits.
