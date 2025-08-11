#!/bin/bash
set -eux
apt-get update -y
apt-get install -y nginx docker.io
systemctl enable nginx && systemctl start nginx
usermod -aG docker ubuntu || true

cat >/etc/nginx/sites-available/studyai <<'NGINX'
server {
  listen 80 default_server;
  server_name _;

  client_max_body_size 20m;

  location / {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
  }
}
NGINX

ln -sf /etc/nginx/sites-available/studyai /etc/nginx/sites-enabled/studyai
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
