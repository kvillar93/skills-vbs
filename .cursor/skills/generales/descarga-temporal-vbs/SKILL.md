---
name: descarga-temporal-vbs
description: >-
  Publica un archivo para descargarlo desde https://vbsolutions.app/descargas/
  y lo borra a los 30 minutos. Usar cuando pidan un enlace, un descargable,
  subirlo a vbsolutions.app, un PDF temporal, o que venza el link.
---

# Descarga temporal en vbsolutions.app

El usuario pide un archivo (PDF u otro) para bajarlo desde **vbsolutions.app**.
El enlace vive **30 minutos** y después el archivo se borra solo.

SSH: skill `ssh-servidores`, alias `vbsolutions`. No imprimas secretos.

## Qué entregar

1. Sube el archivo a `/var/www/descargas/<nombre>.pdf` (nombre corto, sin espacios).
2. Comprueba `curl -sI` y que responda **200**.
3. Pasa en el chat solo esta URL:

`https://vbsolutions.app/descargas/<nombre>.pdf`

4. Di que **vence a los 30 minutos**.
5. Si pide reemplazar o eliminar el anterior, bórralo en el acto. No dejes el archivo viejo.

## Publicar

```powershell
scp -o BatchMode=yes "C:\ruta\archivo.pdf" vbsolutions:/tmp/nombre.pdf
```

```bash
sudo mv /tmp/nombre.pdf /var/www/descargas/nombre.pdf
sudo chown root:www-data /var/www/descargas/nombre.pdf
sudo chmod 644 /var/www/descargas/nombre.pdf
```

El vencimiento usa la fecha de modificación. No vuelvas a tocar el archivo después de moverlo.

## Vencimiento (una sola vez en el servidor)

Si no existe `/etc/cron.d/vbs-descargas`, instálalo. El script del repo es `scripts/vbs-descargas-expirar`.

```bash
sudo sed -i 's/\r$//' /tmp/vbs-descargas-expirar
sudo install -m 755 /tmp/vbs-descargas-expirar /usr/local/bin/vbs-descargas-expirar
sudo tee /etc/cron.d/vbs-descargas >/dev/null << 'EOF'
* * * * * root /usr/local/bin/vbs-descargas-expirar
EOF
sudo chmod 644 /etc/cron.d/vbs-descargas
```

Cada minuto borra lo que lleve **más de 30 minutos** en `/var/www/descargas/`.

## Nginx

`/etc/nginx/sites-available/odoo`, dentro del `server` de `vbsolutions.app`, **antes** de `location /`:

```nginx
location /descargas/ {
    alias /var/www/descargas/;
    autoindex off;
    default_type application/pdf;
    add_header Content-Disposition "attachment";
}
```

Si falta, añádelo, `sudo nginx -t` y `sudo systemctl reload nginx`. No reescribas el resto del sitio.

Directorio: `sudo mkdir -p /var/www/descargas`.
