---
name: atlas-vbs
description: >-
  Opera VBS Atlas (BookStack + theme IA) en el host Docker vbs-trek,
  URL https://atlas.vbsolutions.app. Recolecta metadatos de Odoo por
  cliente, publica documentacion y mantiene el chat de soporte.
  Usar si mencionan Atlas, BookStack interno, atlas.vbsolutions.app
  o documentacion viva de clientes. SSH via ssh-servidores / trek-vbs.
---

# VBS Atlas

Repo privado: https://github.com/kvillar93/vbs-atlas  
Host: `/opt/apps/atlas` en `vbs-trek` (`3.215.189.236`).  
URL: https://atlas.vbsolutions.app

BookStack es imagen upstream `lscr.io/linuxserver/bookstack`. Las modificaciones viven en el theme `themes/atlas` del repo (no forkear el core).

## Layout

```
/opt/apps/atlas/
  docker-compose.yml
  .env                 # 600, no imprimir
  themes/atlas/        # widget y POST /atlas/preguntar
  scripts/
  datos/               # volumen, token API, JSON
  datos/atlas/         # ajustes, ai-key, logs de cron, hashes de modulos
```

Red `proxy` + `VIRTUAL_HOST=atlas.vbsolutions.app`. No publicar 80/443 en el host.

## Recolectar y publicar

En Odoo 16 los textos van en jsonb; `recolectar.py` usa `expr_texto()`. Si el JSON sale con `modulos_instalados=0`, no publiques: el SQL fallo.

Calidad minima (igual que TSHEILA): inventario, customs, menus visibles, personalizaciones, runbook, y fichas de biblioteca con Python/XML. Detalle: `docs/PROCESO-DOCUMENTACION.md`.

```bash
# Desde Trek (preferido)
ssh vbs-trek "python3 /opt/apps/atlas/scripts/cron-atlas.py --ahora --cliente tsheila"

# A mano
scp scripts/recolectar.py scripts/analizar_modulo.py tsheila:/tmp/
ssh tsheila "sudo python3 /tmp/recolectar.py --cliente tsheila --host-publico tsheila.lifterdo.com --modo full --salida /tmp/atlas-tsheila.json"
```

El token esta en `/opt/apps/atlas/datos/api-token.json`. No lo imprimas.

## Chat IA y ajustes

`POST /atlas/preguntar` busca el libro del cliente **y solo** la biblioteca `Modulos Odoo {version}` de ese cliente.  
Ajustes (admin): Configuracion de BookStack → **Atlas**, o `/atlas/ajustes/ia` (AI), `/clientes` y `/cron`. Horario por defecto 1:00 cada 24 h; se puede cambiar por cliente.  
La clave vive solo en el server (`/opt/apps/atlas/datos/atlas/ai-key` o `.env`). Nunca en git ni en el PC.

## Cliente → version → biblioteca

Un cliente = una version mayor de Odoo. El chat no mezcla 14.0 con 16.0.

```
Clientes / TSHEILA          tags: atlas-cliente, odoo-version=14.0, addons-repos=...
Modulos Odoo 14.0 / Odoo 14.0   fichas reutilizables (sale, fleet_rental, ...)
Modulos Odoo 16.0 / Odoo 16.0   otra biblioteca, otro repo (addonsEP16)
```

Al agregar un cliente: Atlas → Ajustes → Clientes (formulario). El cron recolecta en su host y publica. El JSON trae `version_mayor` y `repos`; `publicar.py` etiqueta el libro.

Proceso completo (igual que TSHEILA), para el cron y para otra AI en Cursor: [docs/PROCESO-DOCUMENTACION.md](https://github.com/kvillar93/vbs-atlas/blob/cursor/atlas-bookstack-a569/docs/PROCESO-DOCUMENTACION.md) en el repo `vbs-atlas`.

Sembrar flota: `scripts/descubrir-flota.py` (sonda SSH, no password) y en Trek:

```bash
python3 /opt/apps/atlas/scripts/sembrar-flota.py /opt/apps/atlas/datos/atlas/flota-descubierta.json
# Rehacer solo 16.0 (tras un fix de recolectar):
python3 /opt/apps/atlas/scripts/sembrar-flota.py --solo-version 16.0 --reset-estado
```

## Biblioteca de modulos

`scripts/analizar_modulo.py` + `recolectar.py --modo full|custom` publican fichas reutilizables en el estante `Modulos Odoo X.Y`. El cron mira cada hora quien toca (por defecto 1:00 / 24 h, un cliente a la vez). Calcula hash de custom y de personalizaciones en DB; si alguno cambio, recolecta ambas. Base/enterprise no se re-escanean.

## Reglas

- Solo metadatos de Odoo. Nunca `res_partner`, facturas ni nominas.
- No hagas `grep` del log completo de Odoo.
- No commitees `.env`, PEM ni `datos/`.
