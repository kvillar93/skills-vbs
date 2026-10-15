---
name: crear-compania-odoo
description: >-
  Crea una compañía en un Odoo multicompañía de VBS (ICA y similares) con el
  asistente account_multicompany_easy_creation, logo, external_layout_striped,
  dirección de la compañía de referencia, histórico de tasas, diarios de banco
  con la acción «Crear Diario Banco» y acceso a los usuarios internos. Usar
  cuando pidan dar de alta una empresa, sucursal o persona física en
  ica.vbsolutions.app u otro Odoo que tenga ese módulo.
---

# Crear compañía en Odoo (asistente sencillo)

Conexión: skill `ssh-servidores`. No reinicies Odoo al terminar. No copies el módulo al servidor: el alta es de datos.

## ICA

| Dato | Valor |
|---|---|
| Alias SSH | `ica-vanessa` |
| Host | `ica.vbsolutions.app` |
| Base | `selite` (la única; no se llama `ica`) |
| Odoo | 16. `odoo-bin` en `/odoo/odoo-server/odoo-bin`, conf `/etc/odoo-server.conf` |
| Plan | `account.chart.template` id 1 (`do_chart_template`) |
| Moneda | DOP |
| País | República Dominicana |
| Layout | vista `web.external_layout_striped` |
| Tasas | proveedor `bpd`, intervalo `daily`, base `sellrate` |
| Banco | `Banco Multiple Promerica` |

Antes de escribir, lista `res.company` y confirma que el RNC o la cédula no existan.

## Qué hace el asistente

Modelo `account.multicompany.easy.creation.wiz`, método `action_accept`. Crea la compañía, carga el plan, copia secuencias de la compañía del usuario, ajusta diarios (INV, FACTU, BNK1, CSH1–3) y llama a las retenciones de Ley 30-26 si `dgii_retenciones_30_26` está instalado.

El asistente deja `tipo_itbis_venta = 03` y `clasificacion_itbis_compra = 05`. No pongas bancos en `bank_ids`: el diario se crea después con la acción de servidor.

Desde el shell el usuario es el superusuario y su compañía es la primera. Eso copia secuencias y propiedades desde esa compañía. Al crear, Odoo también enlaza a `__system__`. Quítalo al final para dejar solo usuarios internos activos, igual que el resto de compañías operativas.

## Datos que el asistente no copia

Hay que escribirlos después de `action_accept`:

1. **Dirección completa.** El wizard solo guarda `street`. Copia también `street2`, ciudad, provincia y país del contacto de la compañía de referencia (en ICA, la que tiene «infante» en el nombre: INFANTE CHAIN ADVISORY SRL).
2. **Layout.** `external_report_layout_id` = `env.ref('web.external_layout_striped')`. Es una vista `ir.ui.view`, no un reporte. Copia el `paperformat_id` de la referencia (A4).
3. **Tasas.** `res.currency.rate` es por compañía. Copia todas las tasas de la compañía con el histórico más largo (en ICA, la compañía 1). En las fechas que se solapan, las demás compañías tienen el mismo valor. Deja el proveedor `bpd` / `daily` / `sellrate` para que el cron siga actualizando.
4. **Logo.** `company.logo` en base64. Cuadrado, legible en el encabezado de la factura.
5. **Usuarios.** El wizard recibe los `res.users` con `share = False` (el search ya excluye inactivos). Acceso por `res.company.user_ids`, sin cambiar la compañía por defecto de cada usuario.
6. **Cuentas bancarias.** Ver abajo.

## Cédula y tipo de contribuyente

Guarda el documento solo con dígitos. Una cédula de 11 dígitos (`001-0159033-9` → `00101590339`). Con guiones, la localización la trata como no fiscal.

El cómputo de `l10n_do_dgii_tax_payer_type` compara `l10n_do_default_client` con el texto `fiscal`. En estas bases el valor real es `taxpayer`, así que una cédula queda como `non_payer`. Después del alta, fuerza `taxpayer` en el contacto de la compañía. No hay un valor «RST» en el selección: persona física en régimen simplificado se registra con su cédula y tipo Contribuyente. El contacto de `res.company` se queda `is_company = True`.

## Diarios de banco

La acción de servidor se llama **Crear Diario Banco** y el modelo es `account.account`, no `res.partner.bank`.

1. Crea la cuenta contable `asset_cash` en el grupo Bancos (`code_prefix_start = 110102`).
2. Códigos libres con el patrón de las otras compañías: `110102011`, `110102021`. La acción añade `01` y `02` para recibos y pagos pendientes.
3. El nombre tiene que contener `RD$` o `US$`. La acción no mira `DOP` ni `USD`. Con `RD$` asigna DOP al diario; con `US$`, USD.
4. Pon `currency_id` en la cuenta (la acción no lo hace).
5. Ejecuta la acción con `active_model`, `active_id` y `active_ids`.
6. Crea `res.partner.bank` (número, Promerica, contacto de la compañía, `allow_out_payment`) y asígnalo a `journal.bank_account_id`.

El plan ya deja un diario `BNK1` llamado Bank. No lo borres: las otras compañías creadas con el asistente también lo tienen. Los bancos nuevos salen `BNK2`, `BNK3`, etc.

Nombre que dispara la moneda y se parece a los diarios ya cargados:

```text
Promerica 11810000576196 RD$
Promerica 21021000045347 US$
```

## Shell

En PowerShell no anides comillas. Sube el script con `scp` y ejecútalo con redirección en el servidor:

```powershell
scp -o BatchMode=yes .\crear_compania.py ica-vanessa:/tmp/crear_compania.py
ssh -o BatchMode=yes ica-vanessa "sudo -u odoo /odoo/odoo-server/odoo-bin shell -c /etc/odoo-server.conf -d selite --no-http --workers=0 --max-cron-threads=0 < /tmp/crear_compania.py"
```

El script tiene que hacer `env.cr.commit()` al final. Si falla antes, no deja la compañía a medias. Borra el script y el logo de `/tmp` al terminar.

Esqueleto (el alta real lleva los valores del pedido):

```python
ref = env['res.company'].search([('name', 'ilike', 'infante')])
usuarios = env['res.users'].search([('share', '=', False)])
wiz = env['account.multicompany.easy.creation.wiz'].create({
    'name': 'José Luis Infante Rodríguez',
    'vat': '00101590339',
    'street': ref.partner_id.street,
    'country_id': ref.country_id.id,
    'currency_id': ref.currency_id.id,
    'chart_template_id': 1,
    'user_ids': [(6, 0, usuarios.ids)],
})
wiz.action_accept()
company = wiz.new_company_id
# calle2, layout, tasas, logo, cuentas y accion de servidor
env.cr.commit()
```

## Qué no copiar a mano

Impuestos de ITBIS marcados RST o «N02-05» de venta, y cuentas como `610303012 HONORARIOS POR SERVICIOS PF`, se cargaron después en algunas compañías y no coinciden entre ellas. El asistente ya crea el plan y las retenciones de Ley 30-26. No las dupliques salvo que el pedido lo pida.

## Ejemplo ya hecho (ICA, 2026-10-15)

Compañía **José Luis Infante Rodríguez**, id 5, cédula `00101590339`, dirección de INFANTE CHAIN ADVISORY SRL, layout striped, 690 tasas USD copiadas de la compañía 1, logo JLI / INFANTE.

| Diario | Cuenta | Número Promerica | Moneda |
|---|---|---|---|
| BNK2 | 110102011 | 11810000576196 | DOP |
| BNK3 | 110102021 | 21021000045347 | USD |

Usuarios con acceso: `kvillar@lifterdo.com`, `v.frias@grupocsi.com.do`, `infantechainadvisory@gmail.com`, `i.diaz@grupocsi.com.do`, `a.delossantos@grupocsi.com.do`.
