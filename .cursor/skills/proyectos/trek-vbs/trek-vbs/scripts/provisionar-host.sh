#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
log() { echo "[provision] $*"; }

log "usuario=$(whoami) host=$(hostname)"

if ! sudo swapon --show | grep -q .; then
  log "creando swap 2G"
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi
free -h

log "apt update + paquetes base"
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg ufw

if ! command -v docker >/dev/null 2>&1; then
  log "instalando Docker"
  curl -fsSL https://get.docker.com | sudo sh
fi
sudo usermod -aG docker ubuntu || true
sudo systemctl enable --now docker

log "UFW 22/80/443"
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
sudo ufw status verbose

log "red docker proxy"
sudo docker network inspect proxy >/dev/null 2>&1 || sudo docker network create proxy

sudo mkdir -p /opt/proxy/certs /opt/proxy/vhost.d /opt/proxy/html /opt/proxy/acme /opt/proxy/conf.d
sudo mkdir -p /opt/apps/trek/data /opt/apps/trek/uploads
sudo chown -R ubuntu:ubuntu /opt/proxy /opt/apps

cat > /opt/proxy/docker-compose.yml << 'EOF'
services:
  nginx-proxy:
    image: nginxproxy/nginx-proxy:1.7
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - ./certs:/etc/nginx/certs:rw
      - ./vhost.d:/etc/nginx/vhost.d
      - ./html:/usr/share/nginx/html
      - ./conf.d:/etc/nginx/conf.d
    labels:
      - com.github.nginx-proxy.nginx=true
    networks:
      - proxy
    restart: unless-stopped

  acme:
    image: nginxproxy/acme-companion
    container_name: nginx-proxy-acme
    depends_on:
      - nginx-proxy
    environment:
      DEFAULT_EMAIL: kevin@vbsolutions.info
      NGINX_PROXY_CONTAINER: nginx-proxy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./certs:/etc/nginx/certs:rw
      - ./vhost.d:/etc/nginx/vhost.d
      - ./html:/usr/share/nginx/html
      - ./acme:/etc/acme.sh
    networks:
      - proxy
    restart: unless-stopped

networks:
  proxy:
    name: proxy
    external: true
EOF

cat > /opt/proxy/vhost.d/default << 'EOF'
client_max_body_size 500m;
proxy_read_timeout 86400s;
proxy_send_timeout 86400s;
proxy_buffering off;
EOF

cat > /opt/proxy/vhost.d/trek.vbsolutions.app << 'EOF'
client_max_body_size 500m;
proxy_read_timeout 86400s;
proxy_send_timeout 86400s;
proxy_buffering off;
EOF

cat > /opt/proxy/conf.d/websocket.conf << 'EOF'
send_timeout 86400s;
EOF

cat > /opt/apps/trek/docker-compose.yml << 'EOF'
services:
  app:
    image: mauriceboe/trek:latest
    container_name: trek
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
    tmpfs:
      - /tmp:noexec,nosuid,size=128m
    expose:
      - "3000"
    env_file:
      - .env
    environment:
      - NODE_ENV=production
      - PORT=3000
      - VIRTUAL_HOST=trek.vbsolutions.app
      - VIRTUAL_PORT=3000
      - LETSENCRYPT_HOST=trek.vbsolutions.app
      - LETSENCRYPT_EMAIL=kevin@vbsolutions.info
      - HTTPS_METHOD=redirect
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    networks:
      - proxy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s

networks:
  proxy:
    name: proxy
    external: true
EOF

if [ ! -f /opt/apps/trek/.env ]; then
  ENC=$(openssl rand -hex 32)
  ADMPW=$(openssl rand -base64 24 | tr -d "/+=" | head -c 24)
  umask 077
  cat > /opt/apps/trek/.env << EOF
ENCRYPTION_KEY=${ENC}
TZ=America/Santo_Domingo
LOG_LEVEL=info
ALLOWED_ORIGINS=https://trek.vbsolutions.app
FORCE_HTTPS=true
HSTS_INCLUDE_SUBDOMAINS=false
TRUST_PROXY=1
APP_URL=https://trek.vbsolutions.app
ADMIN_EMAIL=kevin@vbsolutions.info
ADMIN_PASSWORD=${ADMPW}
GEMINI_API_KEY=
EOF
  chmod 600 /opt/apps/trek/.env
  log "creado /opt/apps/trek/.env (secretos no se imprimen)"
else
  log ".env ya existia; no se toca"
fi

cat > /opt/apps/README.md << 'EOF'
# Convencion de deploys en este host (vbs-trek)

IP fija: 3.215.189.236
Dominio raiz: vbsolutions.app
Red Docker compartida: proxy (nginx-proxy + acme-companion)

## Anadir otro proyecto (otro subdominio)

1. DNS A NOMBRE.vbsolutions.app hacia 3.215.189.236 (Route53 zona vbsolutions.app).
2. Crear /opt/apps/NOMBRE/ con su docker-compose.yml.
3. El servicio debe unirse a la red externa proxy (no publicar 80/443).
4. Variables del contenedor de app:
   - VIRTUAL_HOST=NOMBRE.vbsolutions.app
   - VIRTUAL_PORT=<puerto interno>
   - LETSENCRYPT_HOST=NOMBRE.vbsolutions.app
   - LETSENCRYPT_EMAIL=kevin@vbsolutions.info
5. Opcional: /opt/proxy/vhost.d/NOMBRE.vbsolutions.app para body size / websockets.
6. docker compose up -d en esa carpeta. El proxy detecta el contenedor y pide el certificado.

No abras puertos de app en el host. UFW solo 22/80/443.
EOF

log "levantando proxy"
cd /opt/proxy && sudo docker compose pull && sudo docker compose up -d

log "levantando TREK"
cd /opt/apps/trek && sudo docker compose pull && sudo docker compose up -d

log "estado"
sudo docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
log "listo"
