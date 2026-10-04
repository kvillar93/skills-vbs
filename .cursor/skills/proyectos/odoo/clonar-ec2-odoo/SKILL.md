---
name: clonar-ec2-odoo
description: >-
  Clona un servidor EC2 de Odoo para un cliente nuevo o una copia: AMI sin
  reboot, misma llave vbsolutions, stop y start al nacer, IP elastica, registro
  A en vbsolutions.app y SSL nuevo con la direccion del chat. Usar cuando pidan
  crear un server, duplicar un servidor, clonar una EC2, habilitar un cliente
  nuevo o un subdominio .vbsolutions.app.
---

# Clonar EC2 de Odoo

Ejecuta este flujo cada vez que pidan un servidor nuevo o una copia. No improvises otro metodo. La CLI de esta PC ya usa el usuario `kevin-pc`. Region `us-east-1`. Zona `Z02024091P790V5KUMWZ6` (`vbsolutions.app`).

SSH del servidor: skill `ssh-servidores`. Usuario `ubuntu`. Llave `~/.ssh/vbsolutions`.

## Datos que tienen que venir en el chat

No reutilices el ejemplo CSI ni `csi_test`.

| Dato | Si no lo dicen |
|---|---|
| Instancia origen (nombre o id) | Pregunta. Resuelve el id con `aws ec2 describe-instances`. |
| Subdominio o nombre de la instancia | Pregunta. Es el tag `Name`. |
| Direccion del SSL y del DNS | Si solo dan el subdominio, usa `<subdominio>.vbsolutions.app`. Si dan un FQDN, ese es el certificado y el registro A. |
| Llave | `vbsolutions`. Crea otra solo si lo piden en ese mensaje. |

Si el FQDN no termina en `vbsolutions.app`, para y pregunta. Esta zona no sirve para otro dominio.

## Llave

La llave de lanzamiento es `vbsolutions`. No uses `umbrafinance` ni generes un key pair nuevo salvo que el mensaje lo pida.

Si piden una llave nueva: `aws ec2 create-key-pair --key-name NOMBRE --query KeyMaterial --output text` y guardala en `~/.ssh/NOMBRE`. No la pegues en el chat ni en el repo. Pasa `KEY_NAME=NOMBRE` al script y usala en el `ssh -i`.

## Clonado

`bash` no esta en el PATH de PowerShell. Usa Git Bash:

```powershell
$env:SOURCE_INSTANCE_ID = "i-xxxxxxxx"
$env:SUBDOMAIN = "cliente"
$env:DNS_FQDN = "cliente.vbsolutions.app"
& "C:\Program Files\Git\bin\bash.exe" "$env:USERPROFILE\Projects\skills-vbs\.cursor\skills\proyectos\odoo\clonar-ec2-odoo\scripts\clonar-ec2.sh"
```

`scripts/clonar-ec2.sh` hace, en este orden: AMI `--no-reboot`, lanza con el tipo, la subnet y los security groups del origen, espera `running`, **stop**, espera `stopped`, **start**, espera `running` y status ok, IP elastica, UPSERT del A. El tag `Name` es `SUBDOMAIN`.

Si el origen tiene instance profile y `RunInstances` falla por `PassRole`, deten el clonado y dilo. No relances sin el perfil por tu cuenta.

## SSL

El disco trae el certificado y el `server_name` del origen (`/etc/nginx/sites-enabled/odoo`, certbot con plugin nginx). Hay que quitar ese certificado y emitir uno para la direccion del chat.

1. Espera a que el DNS de esa direccion responda la IP elastica (`nslookup`).
2. Entra por la IP, host nuevo:

```bash
ssh -i "$HOME/.ssh/vbsolutions" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 ubuntu@IP "whoami && hostname"
```

3. Anota el certificado viejo: `sudo certbot certificates`.
4. Sustituye el hostname viejo por la direccion nueva en `/etc/nginx/sites-enabled/odoo` (`server_name` y `if ($host = ...)`). `sudo nginx -t && sudo systemctl reload nginx`.
5. Emite el certificado nuevo:

```bash
sudo certbot --nginx -d DIRECCION --non-interactive --agree-tos --redirect
```

6. Borra el certificado clonado, no el nuevo:

```bash
sudo certbot delete --cert-name DOMINIO_VIEJO --non-interactive
sudo nginx -t && sudo systemctl reload nginx
```

7. Comprueba `curl -fsI https://DIRECCION`. El certificado tiene que ser de esa direccion.

Estos servidores traen certbot 0.40. Si `--nginx` no completa el reto HTTP, deja el sitio en el puerto 80 sin las lineas `ssl_certificate` del dominio viejo, recarga nginx y vuelve a lanzar certbot.

## Despues

- Agrega el alias en `~/.ssh/config` (Host, HostName el FQDN, User ubuntu, IdentityFile `C:/Users/kevin/.ssh/vbsolutions`, IdentitiesOnly yes).
- Agrega la fila en `generales/ssh-servidores/hosts.md` y publicala con `scripts/publicar-cambios.ps1` solo si el usuario quiere el inventario en GitHub.
- La copia incluye la base y el filestore del origen. No cambies `web.base.url` ni la base salvo que lo pidan.
- Responde con id de instancia, IP elastica, DNS y el resultado del HTTPS.
