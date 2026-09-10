---
name: trek-vbs
description: >-
  Opera el host Docker VBS TREK (alias vbs-trek, IP 3.215.189.236,
  trek.vbsolutions.app): nginx-proxy + acme-companion, UFW, deploys por
  subdominio y la app TREK. Úsala SIEMPRE si el usuario menciona TREK,
  trek.vbsolutions.app, el conector Gemini, addons de TREK o el alias
  vbs-trek. SSH vía skill ssh-servidores.
---

# TREK VBS (host Docker + app)

Inventario SSH: skill `ssh-servidores` / `hosts.md`.

| Campo | Valor |
|---|---|
| Alias | `vbs-trek` |
| Elastic IP | `3.215.189.236` |
| Usuario | `ubuntu` |
| Hostname EC2 | `ip-172-31-89-134` |
| SO | Ubuntu 26.04 |
| Clave PEM | `vbsolutions` (vault `SSH-Infra`) |
| App | https://trek.vbsolutions.app |
| Addons | https://github.com/kvillar93/trek-addons |

## Conexión

**Local:**

```bash
ssh -o BatchMode=yes -o ConnectTimeout=10 vbs-trek "whoami && hostname"
```

**Cloud Agent / Cursor web** (no hay `~/.ssh/config`):

```bash
bash ~/.cursor/skills/ssh-servidores/scripts/bootstrap_cloud.sh
python3 ~/.cursor/skills/ssh-servidores/scripts/ssh_via_op.py vbs-trek -- whoami && hostname
```

En un worker Windows con PEM local: `ssh -i ~/.ssh/vbsolutions ubuntu@3.215.189.236`.

Confirma usuario `ubuntu` y hostname **antes** de tocar `.env`, UFW o compose.

## Layout del host

```
/opt/proxy/          nginx-proxy + acme-companion (80/443, red `proxy`)
/opt/apps/trek/      app TREK (imagen mauriceboe/trek)
/opt/apps/README.md  convención para el siguiente subdominio
```

- Red Docker **externa** `proxy`. Las apps no publican 80/443 ni el puerto de la app en el host.
- UFW: 22, 80, 443. Swap 2G (caja ~4 GB RAM).
- Secretos de TREK: `/opt/apps/trek/.env` modo `600`. **No** los imprimas.

## Cómo añadir otro proyecto

1. DNS A `NOMBRE.vbsolutions.app` → `3.215.189.236` (Route53, zona `vbsolutions.app`).
2. Carpeta `/opt/apps/NOMBRE/` con `docker-compose.yml`.
3. Unir el servicio a `networks: proxy` (external).
4. En el contenedor: `VIRTUAL_HOST`, `VIRTUAL_PORT`, `LETSENCRYPT_HOST`, `LETSENCRYPT_EMAIL`.
5. Opcional: `/opt/proxy/vhost.d/NOMBRE.vbsolutions.app` (body size, timeouts WS).
6. `docker compose up -d`. El companion pide el certificado solo.

Plantillas: [archivos/CONVENCION-PROXY.md](archivos/CONVENCION-PROXY.md).

## TREK

- Compose: `/opt/apps/trek/docker-compose.yml`
- Datos: `/opt/apps/trek/data` y `uploads`
- Admin inicial: `ADMIN_EMAIL` / `ADMIN_PASSWORD` en `.env` (solo primer boot).
- WebSockets en `/ws`. El vhost ya alarga timeouts y `client_max_body_size 500m`.
- Plugins: Admin → Plugins. Sideload de zip o registry. Conector Gemini: repo `kvillar93/trek-addons`.

```bash
cd /opt/apps/trek && sudo docker compose ps
sudo docker compose logs -n 80 app
# actualizar imagen:
sudo docker compose pull && sudo docker compose up -d
```

No hagas `grep` de `.env`. Para saber qué falta: `grep -E '^[A-Z_]+=' /opt/apps/trek/.env | cut -d= -f1`.

## Variables a rellenar

| Dónde | Variable | Notas |
|---|---|---|
| `/opt/apps/trek/.env` | `GEMINI_API_KEY` | Vacía a propósito. También hay que pegarla cifrada en Admin → Plugins → Conector Gemini (instance settings). |
| Admin TREK | `GEMINI_API_KEY` del plugin | Ahí es de donde el plugin lee (`ctx.config`). |
| Opcional | Unsplash / Google Places / OIDC | Panel de admin de TREK. |

## Addons (sin PRs a liketrek)

Repo propio: https://github.com/kvillar93/trek-addons  
Plugin v1: `gemini-connector` (página + `generateContent` a `generativelanguage.googleapis.com`).  
Skill upstream de plugins: [liketrek/Plugin-Skill](https://github.com/liketrek/Plugin-Skill). Registry comunitario: [TREK-Plugins](https://github.com/liketrek/TREK-Plugins) — **no** abrir PR ahí salvo que el usuario lo pida.

Sideload:

1. En el clone: `npx trek-plugin-sdk pack plugins/gemini-connector`
2. Copiar `plugin.zip` al servidor (p. ej. `/opt/apps/trek/plugins-in/`).
3. Admin → Plugins → instalar zip. Consentir permisos. Pegar `GEMINI_API_KEY`.

## Reglas

- Nunca imprimas PEM, `ENCRYPTION_KEY`, `ADMIN_PASSWORD`, `GEMINI_API_KEY` ni `.env`.
- No abras el puerto 3000 en el host.
- DNS de `*.vbsolutions.app` está en Route53 (NS `awsdns-*`).
- Let's Encrypt: UFW ya abre 80/443. El Security Group de la EC2 (`sg-02d5ca406483902f3`, instancia `i-077b278642a662981`, us-east-1) **aún no** deja entrar 80/443 desde Internet (timeout). Hay que añadir inbound TCP 80 y 443 (0.0.0.0/0) y luego `sudo docker restart nginx-proxy-acme`.
- Plugin `gemini-connector` ya está sideload y **active**. Falta pegar `GEMINI_API_KEY` en Admin → Plugins → instance settings. Zip en `/opt/apps/trek/plugin-gemini-connector.zip`.
