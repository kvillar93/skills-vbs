---
name: collado
description: >-
  Opera Collado (collado.vbsolutions.app, Odoo 14, base colladov1, repo
  addonsce14_collado). Usar al mencionar Collado, CASA ALMACEN HERMANOS
  COLLADO, pedidos compartidos del punto de venta, anular una factura del
  POS y volver a dejar el pedido en borrador para las cajas.
---

# Collado

Odoo 14 Community. Compañía **CASA ALMACEN HERMANOS COLLADO SAS** (id 1). Conexión: skill `ssh-servidores`.

| | |
|---|---|
| Alias | `collado` |
| Host | `collado.vbsolutions.app` |
| Usuario SSH | `ubuntu` |
| SO | Ubuntu 20.04 |
| Base | `colladov1` |
| Servicio | `odoo-server`, usuario de sistema `odoo` |
| Conf | `/etc/odoo-server.conf` |
| Binario | `/odoo/odoo-server/odoo-bin` |
| Addons | `/odoo/odoo-server/addons`, `/odoo/custom/addons`, `/odoo/custom/addons/addonsce14_collado` |

Este cliente no usa `addonsEP16`. El código propio vive en el repo `https://github.com/kvillar93/addonsce14_collado`, rama `master`, clon en `/odoo/custom/addons/addonsce14_collado`. El directorio es de `root`. `git` avisa `dubious ownership`. No ejecutes `git config --global` en el servidor. Si hace falta el remoto, lee `.git/config` con `sudo sed` y no pegues la URL si trae usuario o token.

Local:

```powershell
ssh -o BatchMode=yes collado "whoami && hostname"
```

SQL y el shell de Odoo van por stdin. En PowerShell, here-string simple `@'...'@`. No armes `ssh ... "psql -c \"SELECT ...\""`.

Reiniciar Odoo solo si este chat lo pide, con el alias `restart_odoo` de la skill `ssh-servidores` (dos pasos). Un cambio de datos no necesita reinicio. No despliegues código a este host salvo que este chat lo pida.

## Pedidos compartidos entre cajas

Dos módulos, los dos instalados:

| Módulo | Trabajo |
|---|---|
| `sh_pos_order_list` | Listado. Métodos `search_order` y `search_order_length` en `sh_pos_order_list/models/pos_config.py`. |
| `sh_pos_order_sync` | Envío entre cajas: `assigned_config`, `sh_is_order_send`, `sh_uid`. |

Todas las cajas activas tienen `sh_load_order_by = all` y `user_type = both`. El dominio de `search_order` / `search_order_length` es notación polaca:

```python
['|', ('user_id', '=', uid),
 ('assigned_config', '=', config_id),
 ('state', '!=', 'cancel')]
```

Eso es: (el usuario de la caja es el `user_id` de la orden, o la caja está en `assigned_config`) y la orden no está cancelada. No filtra por sesión.

La tabla es `pos_config_pos_order_rel` (`pos_order_id`, `pos_config_id`).

Para abrirlo en el ticket y cobrarlo o editarlo, el JS exige `state = draft`. Una orden `invoiced` o `paid` sale en el listado y no se recarga al ticket.

Al abrir el listado en `online_mode`, la primera consulta es solo `user_id = usuario de la caja` y `state = draft`. `search_order` (al cambiar de página) y el modo `offline_mode` sí aplican el dominio con `assigned_config`. Un borrador compartido tiene que quedar con el `user_id` del cajero que lo trabajó y con `assigned_config` en las cajas activas.

Las notificaciones en vivo (`bus.bus`) están comentadas en el Python de `sh_pos_order_sync`. Una caja que ya tenía el listado abierto no ve el pedido nuevo hasta recargar el POS.

### Cajas

Los nombres se repiten. Usa el id.

| id | Nombre | Activa | Modo |
|---|---|---|---|
| 1 | Caja 1 | sí | online |
| 3 | Caja 3 | sí | online |
| 5 | Caja 6 | sí | online |
| 7 | Caja 2 | sí | online |
| 8 | Caja 8 | sí | online |
| 9 | Caja 4 | sí | online |
| 10 | Caja 5 | sí | online |
| 11 | Caja 3 | sí | online |

Inactivas: 2 (Caja 2), 4 (Caja 3), 6 (Caja 6). No les asignes pedidos.

Un borrador que las cajas pueden retomar lleva:

- `state = draft`, `name = '/'`, `amount_paid = 0`, `amount_return = 0`
- `sh_is_order_send = true`, `is_edit = false`, `is_partial = false`
- `to_invoice = false`, `account_move` vacío
- `l10n_latam_document_number` vacío (si queda el NCF, la próxima factura lo reutiliza)
- `sh_uid` único y cada línea con `sh_line_id` único
- `assigned_config` = las 8 cajas activas
- impuestos de la línea en `account_tax_pos_order_line_rel` (impuesto 1, Exento ITBIS Ventas; impuesto 4, 18% ITBIS Incl. Ventas)
- la línea marcada `*ELIMINADO*` en `add_section`, si el pedido original la tenía

`bi_pos_pay_later` está instalado. `wk_pos_partial_payment` no. Si `name = '/'` e `is_partial` es true, el `write` de ese módulo consume la secuencia de la caja. Una orden anulada no debe quedarse con `name = '/'`.

Al crear una sesión, ese módulo mueve a la sesión nueva los borradores del mismo usuario cuya sesión anterior ya está cerrada.

## Anular la factura y devolver el pedido al POS

La factura fiscal no se anula con `button_cancel` directo. En `l10n_do_accounting` eso abre el wizard `account.move.cancel` (`wizard/account_move_cancel.py`). Una factura a la vez. Solo si `payment_state` es `not_paid`. Escribe `cancellation_type` y `state = cancel`. No crea nota de crédito. El NCF queda consumido.

El efectivo del POS está en `pos_payment` hasta el cierre. La factura puede estar `posted` y `not_paid` aunque el ticket diga Efectivo.

`bi_pos_pay_later._accumulate_amounts` recorre las órdenes de la sesión con `is_partial = false`. Suma los pagos. Si hay `account_move`, mete el por cobrar (aunque la factura esté cancelada) a la conciliación del cierre. Si no hay factura, contabiliza las líneas como venta. El efectivo esperado de la sesión sale de `pos.payment` por `session_id`, aparte de ese filtro.

Para rehacer un pedido ya facturado, en el shell de Odoo y en una sola transacción:

1. Anula la factura con el wizard, tipo `04` (corrección de información del producto) cuando el motivo es volver a facturar el mismo pedido.
2. Duplica la orden (`copy`) en borrador con los campos de arriba. Borra los `pos.payment` que el `copy` haya arrastrado. Deja `pos_reference` reconocible y único. Copia líneas, impuestos y `assigned_config`.
3. En la orden original: borra su `pos.payment`, `amount_paid = 0`, `state = cancel`, `is_partial = true`, `sh_is_order_send = false`, `name` distinto de `/`. Deja `account_move` apuntando a la factura cancelada y las líneas intactas.

`is_partial = true` saca la orden original del cierre. Sin el pago, el efectivo de la sesión no sigue contando esos RD$. El borrador nuevo es el que el cajero cobra otra vez, y `l10n_do_pos` asigna el NCF siguiente al facturar.

No pongas la orden original en otra sesión ya cerrada.

### Caso 23 de octubre de 2026

Ticket: Orden 09856-001-0006, NCF B0100017032, BOTICA LA BENDICION DE DIOS BBD SRL (RNC 133079771), RD$ 4,046.18, efectivo, cajero Miguelito.

| Qué | Id | Quedó |
|---|---|---|
| Factura `INV/2026/8864` | `account.move` 73579 | `cancel`, tipo 04, NCF B0100017032 |
| Pedido original | `pos.order` 46135 | `cancel`, `is_partial`, sin pago, referencia `Orden 09856-001-0006 (NCF B0100017032 anulada)` |
| Pedido para las cajas | `pos.order` 46137 | `draft`, referencia `Orden 09856-001-0006`, total 4046.18, usuario `cajero2` (id 7), sesión 9856 (`POS/09799`, Caja 2) |

Para verlo: recargar el POS y abrir el listado de pedidos. Con `cajero2` en Caja 2 aparece al entrar. Cliente BOTICA LA BENDICION DE DIOS BBD SRL, RD$ 4,046.18, borrador.

## Consultas

```sql
SELECT am.id, am.name, am.state, am.ref, am.payment_state, am.amount_total, am.cancellation_type
FROM account_move am
WHERE am.ref = 'B0100017032' OR am.name = 'INV/2026/8864';

SELECT po.id, po.pos_reference, po.state, po.amount_total, po.amount_paid,
       po.user_id, po.session_id, po.account_move, po.sh_is_order_send, po.is_partial
FROM pos_order po
WHERE po.pos_reference ILIKE '%09856-001-0006%'
   OR po.account_move = 73579;
```
