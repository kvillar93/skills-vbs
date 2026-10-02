---
name: facturas-borrador-lifter
description: >-
  Confirma las facturas de cliente en borrador de LIFTER (lifterdo.com, base
  lifter) y las envía por correo al cliente y a sus contactos hijos. Usar
  cuando pidan confirmar, publicar o enviar facturas en borrador de Lifter,
  el día 2 de cada mes, o al mencionar INV de LIFTER SRL y el botón de
  enviar factura.
---

# Facturas en borrador de Lifter

Servidor `lifter` (`lifterdo.com`). Base `lifter`. Odoo 14, compañía LIFTER SRL. Conexión: skill `ssh-servidores`.

Solo facturas de cliente (`out_invoice`) en `draft`. No toques asientos (`entry`), facturas de proveedor (`in_invoice`) ni notas de crédito.

## Qué hace el botón

El módulo `invoice_mass_mailing` no está instalado. El envío es el wizard estándar `account.invoice.send` (botón Enviar e imprimir), solo correo, sin imprimir.

Dos automatizaciones de Odoo no corren solas desde el shell:

| Automatización | Cuándo | Qué hacer en el shell |
|---|---|---|
| Account Invoice Send | on_change del wizard | Poner `partner_ids` = `partner_id.child_ids` + `partner_id` |
| Create Email | al crear `mail.mail` de `account.move` | No tocar `email_from`. Deja el remitente `LIFTER SRL <kvillar@lifterdo.com>` |

Enviar como el usuario `kvillar@lifterdo.com` (id 2) para que el autor del mensaje sea Kevin Villar. Los seguidores de la factura también reciben copia; no los quites.

El correo de un hijo puede estar mal escrito (por ejemplo con prefijo `mailto:`). Inclúyelo igual que la automatización y repórtalo.

## Alcance

- Pedido de prueba, o la primera vez en un chat: solo la factura draft de menor `id`. Confirma, envía, informa y espera.
- El usuario dice que sigas con el resto, o la corrida es la del día 2: todas las `out_invoice` en draft.
- Variable `SOLO_ID` en el comando limita a una factura.

Confirmar publica el e-CF en la DGII. Es definitivo si la DGII acepta. Si rechaza, el módulo cancela la factura: no envíes correo. Si queda `delivered_pending`, el script consulta el track id una vez.

## Ejecutar

El script vive junto a esta skill: `scripts/enviar_borradores.py`. Se mete por stdin al shell de Odoo. No lo pegues en el argumento de `ssh`.

Local (Windows):

```powershell
Get-Content -Raw "$env:USERPROFILE\.cursor\skills\proyectos\odoo\facturas-borrador-lifter\scripts\enviar_borradores.py" | ssh -o BatchMode=yes lifter "sudo -u odoo env PYTHONUNBUFFERED=1 /odoo/odoo-server/odoo-bin shell -c /etc/odoo-server.conf -d lifter --no-http --workers=0 --max-cron-threads=0"
```

Una sola factura: añade `SOLO_ID=<id>` dentro del `env` del comando remoto.

Nube (Cloud Agent): `bootstrap_cloud.sh` y luego el mismo stdin con `ssh_via_op.py lifter -- sudo -u odoo env PYTHONUNBUFFERED=1 /odoo/odoo-server/odoo-bin shell -c /etc/odoo-server.conf -d lifter --no-http --workers=0 --max-cron-threads=0`.

El shell tarda unos 15 s por factura. Espera a que termine.

## Cómo leer la salida

- `POSTED` + `delivered_accepted` o `conditionally_accepted`: publicada y aceptada.
- `ENVIO` con `sent`: correo aceptado por el servidor. Lista cada correo.
- `NO_EMAIL`: publicada pero la DGII no la aceptó. No reintentes el correo.
- `ERROR_POST` / `ERROR_MAIL`: esa factura falló; las demás siguen.
- `BORRADORES_RESTANTES 0`: no quedan facturas de cliente en borrador.

Responde en español con una tabla: número, NCF (`ref`), cliente, correos y estado. Menciona copias a seguidores y correos mal formados.

## Automatización de Cursor

Corrida mensual, día 2 a las 8:00. Sin repositorio. Instrucción: seguir esta skill y `ssh-servidores`, procesar todas las facturas de cliente en borrador (sin prueba de una) y dejar la tabla de resultado. Hace falta la skill sincronizada para Cloud Agents y el secreto `OP_SERVICE_ACCOUNT_TOKEN`. Crear la automatización desde la ventana de Agents; esta sesión de worker no abre el editor.
