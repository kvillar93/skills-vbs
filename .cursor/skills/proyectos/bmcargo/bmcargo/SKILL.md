---
name: bmcargo
description: >-
  Opera BMCargo en bmcvmod (Odoo 16, base bmc): sync de facturas desde SQL
  Server (sync_objects / sync_objects_vbs) y facturas cruzadas entre la
  empresa madre y las agencias (account_inter_company_vbs). Usar al mencionar
  bmcvmod, BMCargo, BUSINESS MAIL & CARGO, San Juan, Barahona, sucursales
  relacionadas, reemision de facturas o facturas de proveedor entre companias.
---

# BMCargo (bmcvmod)

Odoo 16 en el alias `bmcvmod`. Base `bmc`. Conexion: skill `ssh-servidores`.

| | |
|---|---|
| Alias | `bmcvmod` |
| Host | `34.66.100.94` |
| Usuario SSH | `kvillar` |
| SO | Ubuntu 20.04 |
| Servicio | `odoo-server`, usuario de sistema `odoo` |
| Conf | `/etc/odoo-server.conf` |
| Binario | `/odoo/odoo-server/odoo-bin` |
| Addons propios | `/odoo/custom/addons/bmc/kvillar93/bmcargo_vbs` y `/odoo/custom/addons/bmc/sync_objects` |

Local:

```powershell
ssh -o BatchMode=yes bmcvmod "whoami && hostname"
```

Cloud Agent: `bootstrap_cloud.sh` y `ssh_via_op.py bmcvmod`. La PEM `private_odoo` tiene que estar en el vault `SSH-Infra`. `bmcvmod-test` (`34.57.162.99`) en octubre 2026 no contestaba el puerto 22.

SQL y el shell de Odoo van por stdin. En PowerShell, here-string simple `@'...'@`. No armes `ssh ... "psql -c \"SELECT ...\""`.

Reiniciar Odoo solo si este chat lo pide, con el alias `restart_odoo` de la skill `ssh-servidores` (dos pasos). No uses `systemctl restart` por tu cuenta.

## Dos modulos, dos trabajos

No los mezcles.

| Modulo | Trabajo |
|---|---|
| `sync_objects` + `sync_objects_vbs` | Trae facturas y pagos del SQL Server de BMC a Odoo. Modelo `sync.object`. El wizard `sync.invoice.resync.wizard` vuelve a leer numeros `NumeroFT` que faltan en Odoo. |
| `account_inter_company_vbs` | Al confirmar una factura, si el contacto es una compania o esta en **Sucursales relacionadas**, crea la factura inversa en la otra compania. |

La reemision de una factura que ya existe en la madre y falta como factura de proveedor en la agencia es el segundo modulo. El wizard de resync no sirve para eso: la factura de cliente ya esta en Odoo.

## Companias

La madre que factura a las agencias es **BUSINESS MAIL & CARGO SRL** (id 2, RNC `101668695`). Las agencias son otras `res.company` con `rule_type = invoice_and_refund`.

San Juan es **AGENCIA BMC SAN JUAN DE LA MAGUANA** (id 20, RNC `132557018`). En Sucursales relacionadas tiene, entre otros:

| partner_id | Contacto | Para que sirve |
|---|---|---|
| 127428 | Agencia Bmc Barahona (SAN JUAN BM CARGO, SRL) | Mismo RNC `132557018`. Facturas de BMC a este contacto deben nacer como `in_invoice` en San Juan. |
| 11030 | AGENCIA BMC BANI (TPL Trade Protect Logistics, SRL) | Igual, hacia San Juan. |

El RNC del encabezado de un estado de Barahona puede ser el de San Juan. El contacto de la factura es Barahona; la compania que recibe la factura de proveedor es San Juan.

Listar relaciones:

```sql
SELECT r.company_id, c.name AS compania, r.partner_id, p.name AS sucursal, p.vat
FROM sucursal_relacionada_rel r
JOIN res_company c ON c.id = r.company_id
JOIN res_partner p ON p.id = r.partner_id
WHERE c.id = 20
ORDER BY p.name;
```

`_find_company_from_partner` busca primero `res.company.partner_id`. Si no hay compania con ese contacto, busca `sucursal_relacionada_rel`. Sin esa fila, la factura de la madre se confirma y no crea nada en la agencia. Agregar la relacion despues no rellena el pasado.

## Que crea la intercompania

Al confirmar (`_post`) una `out_invoice` de la madre:

- Compania destino: la de la sucursal relacionada.
- Tipo: `in_invoice` (factura de proveedor).
- Contacto: el partner de la madre (BUSINESS MAIL & CARGO SRL).
- Copia `id_factura` (NumeroFT, por ejemplo `FT40-2198576`), `l10n_do_fiscal_number` (e-CF), fecha e importes.
- En San Juan el diario de compras con documentos es **Facturas de proveedores** (id 741). El nombre queda `FACTU/AAAA/xxxx`.
- `auto_generated = true`, `auto_invoice_id` apunta a la factura de la madre y `related_auto_invoice_id` de la madre apunta a la de proveedor.
- La publica (`_post`). Como `auto_generated` es verdadero, no genera otra factura de vuelta.

No corre si `related_auto_invoice_id` ya tiene valor, si `sync_id.sync_importador` es verdadero, o si `x_run_intercompany` es verdadero. Tampoco si ya hay en la compania destino una factura no cancelada del mismo tipo con el mismo `id_factura` o el mismo NCF y el contacto comercial de la madre.

## Reemitir facturas de proveedor

Cuando la sucursal ya esta relacionada y hay facturas de cliente posteadas en la madre sin factura de proveedor.

1. Confirma la fila en `sucursal_relacionada_rel`. Si falta, no la inventes: pidela. Borrar o cambiar relaciones contables pide confirmacion.
2. Lista las `out_invoice` posteadas de la madre (`company_id = 2`) de ese `partner_id`, en el rango pedido, con `related_auto_invoice_id` nulo.
3. Confirma que en la agencia no exista ya ese `id_factura` ni ese `l10n_do_fiscal_number` (cualquier estado distinto de `cancel`).
4. Lee `period_lock_date`, `fiscalyear_lock_date` y `tax_lock_date` de la agencia. Si hay cierre que tape la fecha, para y avisa.
5. Prueba **una** factura (la de menor monto del rango). Si el destino queda `posted`, el monto cuadra a 0.02 y el `id_factura` es el mismo, sigue con el resto.
6. Un `partner_id` por llamada. El contexto lleva `related_sucursal_id` de ese contacto.

Shell (sustituye los ids). Usuario intercompania de San Juan: id 1 (`__system__`).

```powershell
$py = @'
ids = []  # account.move id de la madre, un solo partner
company = env['res.company'].browse(20)
user = company.intercompany_user_id
ctx = dict(env.context, default_company_id=company.id, related_sucursal_id=127428)
ctx.pop('default_journal_id', None)
moves = env['account.move'].browse(ids).exists()
faltan = moves.filtered(lambda m: not m.related_auto_invoice_id and m.state == 'posted' and m.move_type == 'out_invoice')
created = faltan.with_user(user).with_context(ctx).with_company(company)._inter_company_create_invoices()
errores = 0
for m in faltan:
    dest = m.related_auto_invoice_id
    ok = (
        dest and dest.state == 'posted' and dest.company_id.id == company.id
        and dest.move_type == 'in_invoice'
        and abs(dest.amount_total - m.amount_total) < 0.02
        and dest.id_factura == m.id_factura
    )
    print('OK' if ok else 'DIFIERE', m.id_factura, m.name, float(m.amount_total), dest.name if dest else None)
    if not ok:
        errores += 1
print('CREADAS', len(created), 'ERRORES', errores)
if errores:
    env.cr.rollback()
else:
    env.cr.commit()
'@
$py | ssh -o BatchMode=yes bmcvmod "sudo -u odoo env PYTHONUNBUFFERED=1 /odoo/odoo-server/odoo-bin shell -c /etc/odoo-server.conf -d bmc --no-http --workers=0 --max-cron-threads=0"
```

El registry tarda unos 15 s. El lote de 17 facturas de octubre 2026 tardo unos 50 s. No hagas commit si algun monto no cuadra.

Consulta de faltantes:

```sql
SELECT am.id, am.name, am.id_factura, am.l10n_do_fiscal_number,
       am.invoice_date, am.amount_total
FROM account_move am
WHERE am.company_id = 2
  AND am.partner_id = 127428
  AND am.move_type = 'out_invoice'
  AND am.state = 'posted'
  AND am.invoice_date >= '2026-09-01'
  AND am.related_auto_invoice_id IS NULL
ORDER BY am.invoice_date, am.id;
```

## Caso San Juan / Barahona (2026-10-06)

Faltaba la relacion de San Juan con el contacto Barahona. Ya estaba creada al ejecutar (partner 127428 en la compania 20). Bani, en el mismo rango, ya tenia sus 34 facturas de proveedor.

Se reemitieron las `out_invoice` de BMC hacia Barahona del 1 de septiembre de 2026 a la fecha. Eran 18, todas posteadas, ninguna con `related_auto_invoice_id`. Total **77,765.79**, igual en San Juan. Diario Facturas de proveedores, contacto BUSINESS MAIL & CARGO SRL, estado `posted`.

Las 13 del estado de cuenta (14 al 29 de septiembre) suman 53,694.26. Las otras cinco llegan hasta el 5 de octubre. No habia facturas de Barahona entre el 1 y el 13 de septiembre.

| NumeroFT | Fecha | Monto | Factura madre | Factura proveedor San Juan |
|---|---|---:|---|---|
| FT40-2198576 | 2026-09-14 | 427.81 | INV/2026/21006 | FACTU/2026/2140 |
| FT40-2198671 | 2026-09-15 | 2,681.53 | INV/2026/21101 | FACTU/2026/2141 |
| FT40-2198815 | 2026-09-16 | 1,173.65 | INV/2026/21161 | FACTU/2026/2142 |
| FT40-2198857 | 2026-09-17 | 8,370.92 | INV/2026/21305 | FACTU/2026/2143 |
| FT40-2198944 | 2026-09-18 | 7,568.83 | INV/2026/21402 | FACTU/2026/2144 |
| FT40-2199071 | 2026-09-19 | 1,346.83 | INV/2026/21432 | FACTU/2026/2145 |
| FT40-2199140 | 2026-09-21 | 7,225.62 | INV/2026/21523 | FACTU/2026/2146 |
| FT40-2199197 | 2026-09-22 | 6,646.44 | INV/2026/21652 | FACTU/2026/2147 |
| FT40-2199331 | 2026-09-23 | 5,189.27 | INV/2026/21707 | FACTU/2026/2148 |
| FT40-2199418 | 2026-09-25 | 5,090.13 | INV/2026/21796 | FACTU/2026/2149 |
| FT40-2199522 | 2026-09-26 | 4,436.26 | INV/2026/21872 | FACTU/2026/2150 |
| FT40-2199656 | 2026-09-28 | 369.03 | INV/2026/22038 | FACTU/2026/2151 |
| FT40-2199705 | 2026-09-29 | 3,167.94 | INV/2026/22158 | FACTU/2026/2152 |
| FT40-2199823 | 2026-10-01 | 6,508.17 | INV/2026/22357 | FACTU/2026/2153 |
| FT40-2199976 | 2026-10-02 | 5,854.00 | INV/2026/22472 | FACTU/2026/2154 |
| FT40-2200125 | 2026-10-03 | 5,706.45 | INV/2026/22502 | FACTU/2026/2155 |
| FT40-2200188 | 2026-10-04 | 680.43 | INV/2026/22619 | FACTU/2026/2156 |
| FT40-2200368 | 2026-10-05 | 5,322.48 | INV/2026/22690 | FACTU/2026/2157 |

## Resync desde SQL Server

Solo si el NumeroFT no existe como factura en Odoo. El `sync.object` de esa fecha y compania abre el wizard **Resincronizar Facturas / Pagos**:

- Por numeros: `action_resync_by_invoice_numbers` (NumeroFT separados por coma).
- Faltantes del dia: `action_resync_missing_for_day`, usa `sync.object.date`.

La conexion SQL Server sale de `ir.config_parameter` (`sync_objects.sync_host` y el resto). No imprimas el password ni el valor de `sync_objects.sync_passw`.

## Que no hacer

- No reemitir con el wizard de resync una factura que ya esta en la madre.
- No confirmar otra vez la factura de la madre para disparar la intercompania: ya esta `posted` y un segundo `_post` no rehace el enlace.
- No insertes `account_move` por SQL.
- No toques facturas de Bani u otra sucursal si el pedido es solo Barahona. Antes del lote, agrupa por `partner_id` y ensena cuantas faltan.
- Logs de Odoo: `sudo ls -lh` y `sudo tail -c`, nunca `grep` del archivo completo.
