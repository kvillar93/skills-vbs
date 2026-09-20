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

```bash
scp scripts/recolectar.py tsheila:/tmp/atlas-recolectar.py
ssh tsheila "sudo python3 /tmp/atlas-recolectar.py --cliente tsheila --host-publico tsheila.lifterdo.com --salida /tmp/atlas-tsheila.json"
python scripts/publicar.py --json datos/tsheila.json --base https://atlas.vbsolutions.app --token-id ... --token-secret ...
```

El token esta en `/opt/apps/atlas/datos/api-token.json`. No lo imprimas.

## Chat IA y ajustes

`POST /atlas/preguntar` busca el libro abierto **y** la biblioteca `Modulos Odoo {version}`.  
Ajustes (admin): https://atlas.vbsolutions.app/atlas/ajustes — token AI, modelo, cron y log.  
La clave vive solo en el server (`/opt/apps/atlas/datos/atlas/ai-key` o `.env`). Nunca en git ni en el PC.

## Biblioteca de modulos

`scripts/analizar_modulo.py` + `recolectar.py --modo full|custom` publican fichas reutilizables en el estante `Modulos Odoo X.Y`. El cron (`scripts/cron-atlas.sh` cada 15 min, respeta el intervalo) solo relee `/odoo/custom/addons` si el hash cambio. Base/enterprise no se re-escanean.

## Reglas

- Solo metadatos de Odoo. Nunca `res_partner`, facturas ni nominas.
- No hagas `grep` del log completo de Odoo.
- No commitees `.env`, PEM ni `datos/`.
