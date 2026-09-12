# Convención nginx-proxy + ACME (vbs-trek)

Red Docker `proxy` (externa). Un solo nginx en 80/443. Cada app es un compose en `/opt/apps/<slug>/`.

## Contenedor de aplicación

```yaml
services:
  app:
    image: ejemplo/app:latest
    expose:
      - "8080"
    environment:
      VIRTUAL_HOST: nombre.vbsolutions.app
      VIRTUAL_PORT: "8080"
      LETSENCRYPT_HOST: nombre.vbsolutions.app
      LETSENCRYPT_EMAIL: kevin@vbsolutions.info
      HTTPS_METHOD: redirect
    networks:
      - proxy
    restart: unless-stopped

networks:
  proxy:
    name: proxy
    external: true
```

No mapees `80:80` ni `443:443` en la app. Eso es solo del proxy en `/opt/proxy`.

## Vhost extra (WebSocket / body grande)

`/opt/proxy/vhost.d/nombre.vbsolutions.app`:

```
client_max_body_size 500m;
proxy_read_timeout 86400s;
proxy_send_timeout 86400s;
proxy_buffering off;
```

## DNS

Registro A en Route53 (zona `vbsolutions.app`) hacia la Elastic IP `3.215.189.236`. El companion no emite certificado hasta que Let's Encrypt pueda resolver y llegar al puerto 80.
