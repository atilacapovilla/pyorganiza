# Deploy do PyOrganiza na DigitalOcean — Passo a Passo Completo

**Versão:** 2.0  
**Última atualização:** 03/07/2026  
**Stack:** Django 5.2, PostgreSQL 16, Nginx, Docker, Gunicorn  
**SO:** Ubuntu 24.04 LTS

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Preparação do Projeto Local](#2-preparação-do-projeto-local)
3. [Criando o Droplet na DigitalOcean](#3-criando-o-droplet-na-digitalocean)
4. [Configuração Inicial do Servidor](#4-configuração-inicial-do-servidor)
5. [Segurança e Hardening](#5-segurança-e-hardening)
6. [Instalação do Docker e Docker Compose](#6-instalação-do-docker-e-docker-compose)
7. [Clonando o Repositório e Configurando Variáveis](#7-clonando-o-repositório-e-configurando-variáveis)
8. [Configurando Nginx e SSL com Let's Encrypt](#8-configurando-nginx-e-ssl-com-lets-encrypt)
9. [Fazendo o Deploy dos Containers](#9-fazendo-o-deploy-dos-containers)
10. [Pós-Deploy](#10-pós-deploy)
11. [Comandos de Manutenção](#11-comandos-de-manutenção)
12. [Atualizando o Projeto](#12-atualizando-o-projeto)
13. [Backup e Restauração](#13-backup-e-restauração)
14. [Monitoramento](#14-monitoramento)
15. [Rollback](#15-rollback)
16. [Troubleshooting](#16-troubleshooting)
17. [Referências](#17-referências)

---

## 1. Pré-requisitos

### 1.1 Conta na DigitalOcean
- Acesse [cloud.digitalocean.com](https://cloud.digitalocean.com) e crie uma conta
- Adicione crédito ou verifique seu plano atual

### 1.2 Domínio (recomendado)
- Um domínio próprio (ex: `seudominio.com`) apontado para a DigitalOcean
- Se não tiver, o deploy funciona com IP, mas **SSL não será possível**

### 1.3 Ferramentas Locais
- **Git**: `git --version`
- **SSH**: `ssh -V` (já vem instalado no Linux/macOS)
- **Chave SSH** configurada: `ls -la ~/.ssh/` (deve conter `id_rsa.pub` ou `id_ed25519.pub`)

  ```bash
  # Se não tiver, gere uma:
  ssh-keygen -t ed25519 -C "seu-email@exemplo.com"
  ```

### 1.4 Repositório Git
O código deve estar em um repositório remoto (GitHub, GitLab, etc.) para clonar no servidor.

```bash
# Se ainda não fez:
git remote add origin https://github.com/seu-usuario/pyorganiza.git
git push -u origin main
```

---

## 2. Preparação do Projeto Local

### 2.1 Arquivos de deploy já inclusos

| Arquivo | Função |
|---------|--------|
| `Dockerfile` | Imagem Python 3.11-slim com dependências do WeasyPrint |
| `docker-compose.yml` | Orquestração: Django app + PostgreSQL 16 + Nginx |
| `nginx/nginx.conf` | Reverse proxy com cache de estáticos/media e suporte SSL |
| `.env.prod` | Template de variáveis de ambiente de produção |

### 2.2 Gerar SECRET_KEY para produção

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Exemplo de saída:
```
d%#k9$2&x@m!q#p8v7n6b5$4r3t2y1u0i9o8i7u6y5t4r3e2w1q
```

Guarde esse valor — será usado no `.env.prod` do servidor.

### 2.3 Verificar .gitignore

Confirme que estes arquivos estão no `.gitignore` (já configurado):

```gitignore
.env
.env.prod
db.sqlite3
venv/
```

### 2.4 Commit final antes do deploy

```bash
git add .
git commit -m "chore: prepara arquivos para deploy docker"
git push origin main
```

---

## 3. Criando o Droplet na DigitalOcean

### 3.1 Escolher configuração

1. Acesse [cloud.digitalocean.com](https://cloud.digitalocean.com)
2. Clique em **"Create"** → **"Droplets"**
3. Configure:

| Campo | Valor | Motivo |
|-------|-------|--------|
| **Image** | **Ubuntu 24.04 LTS** | Estável e com suporte de longo prazo |
| **Plan** | **Basic → Regular → 4 GB / 2 CPUs** | Mínimo para WeasyPrint + Django + PostgreSQL |
| **CPU options** | Intel ou AMD (padrão) | — |
| **Datacenter region** | **NYC1** ou **TOR1** (mais próximos do Brasil) | Menor latência para usuários brasileiros |
| **VPC** | Default | — |
| **Authentication** | **SSH keys** | Adicione sua chave pública (`~/.ssh/id_ed25519.pub`) |
| **Hostname** | `pyorganiza` | Nome do droplet |
| **Backups** | Ativar (~20% extra) | Recomendado para produção |
| **Monitoring** | Ativar | Métricas de CPU/memória no painel DO |

> ⚠️ **4 GB RAM é o mínimo.** O WeasyPrint (geração de PDF) pode consumir 1-2 GB por requisição. Com 2 GB o container será morto por OOM (Out Of Memory).

### 3.2 Adicionar chave SSH (se não estiver no painel)

No painel da DigitalOcean:
- **Settings → Security → SSH Keys → Add SSH Key**
- Cole o conteúdo de `~/.ssh/id_ed25519.pub` (ou `~/.ssh/id_rsa.pub`)

### 3.3 Criar o droplet

Clique em **"Create Droplet"** e aguarde 30-60 segundos.

### 3.4 Anotar o IP

Após criar, anote o **endereço IPv4** do droplet (ex: `142.93.xxx.xxx`).

### 3.5 Configurar DNS (se tiver domínio)

Se você tiver um domínio, aponte-o para o IP do droplet:

1. No painel da DigitalOcean: **Networking → Domains**
2. Adicione seu domínio (ex: `seudominio.com`)
3. Crie um registro **A**:
   - **Hostname:** `@` (ou `pyorganiza` para subdomínio)
   - **Will direct to:** IP do droplet
   - **TTL:** 3600 (padrão)

A propagação DNS pode levar de alguns minutos a algumas horas.

---

## 4. Configuração Inicial do Servidor

### 4.1 Acessar o servidor via SSH

```bash
ssh root@<IP_DO_DROPLET>
```

> **Dica:** O IP está no painel DO → Droplets → pyorganiza → IP Address.

### 4.2 Atualizar todos os pacotes

```bash
apt update && apt upgrade -y
```

### 4.3 Criar usuário não-root

```bash
adduser deploy
# Defina uma senha forte e preencha as informações (pode pular com Enter)
```

Adicionar ao grupo sudo:

```bash
usermod -aG sudo deploy
```

### 4.4 Configurar acesso SSH para o usuário deploy

```bash
# Copiar chave SSH do root para o novo usuário
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy/
```

Testar o acesso (em um novo terminal):

```bash
ssh deploy@<IP_DO_DROPLET>
```

### 4.5 Desabilitar login como root (opcional, mas recomendado)

```bash
sudo sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

> ⚠️ Antes de sair da sessão root, **teste o SSH como `deploy`** em outro terminal para não ficar bloqueado.

### 4.6 Configurar timezone e locale

```bash
sudo timedatectl set-timezone America/Sao_Paulo
```

```bash
sudo apt install -y locales
sudo locale-gen pt_BR.UTF-8
```

### 4.7 Configurar firewall (UFW)

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
# Deve mostrar:
# OpenSSH                   ALLOW       Anywhere
# 80/tcp                    ALLOW       Anywhere
# 443/tcp                   ALLOW       Anywhere
```

### 4.8 Otimizar o sistema

```bash
# Aumentar o limite de arquivos abertos (útil para o PostgreSQL)
echo "fs.file-max = 100000" | sudo tee -a /etc/sysctl.conf
echo "deploy soft nofile 65535" | sudo tee -a /etc/security/limits.conf
echo "deploy hard nofile 65535" | sudo tee -a /etc/security/limits.conf

# Aplicar
sudo sysctl -p

# Configurar swap (essencial para evitar OOM com WeasyPrint)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Tornar permanente
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verificar
free -h
#              total        used        free      shared  buff/cache   available
# Mem:          3.8G        300M        2.5G        1.2M        1.0G        3.2G
# Swap:         2.0G          0B        2.0G
```

---

## 5. Segurança e Hardening

### 5.1 fail2ban — Proteção contra força bruta

```bash
sudo apt install -y fail2ban
```

Criar configuração local:

```bash
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
```

Configurar para SSH:

```bash
sudo tee /etc/fail2ban/jail.d/sshd.local <<EOF
[sshd]
enabled = true
port = ssh
maxretry = 5
bantime = 3600
findtime = 600
EOF
```

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo fail2ban-client status
```

### 5.2 unattended-upgrades — Atualizações automáticas de segurança

```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
# Selecione "Yes" quando perguntar sobre atualizações automáticas
```

### 5.3 Configurar horário do cron para fuso brasileiro

```bash
echo "TZ=America/Sao_Paulo" | sudo tee -a /etc/crontab
```

---

## 6. Instalação do Docker e Docker Compose

### 6.1 Remover versões antigas (se houver)

```bash
for pkg in docker.io docker-doc docker-compose podman-docker containerd runc; do sudo apt remove -y $pkg; done
```

### 6.2 Instalar dependências

```bash
sudo apt install -y ca-certificates curl gnupg
```

### 6.3 Adicionar repositório oficial do Docker

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 6.4 Instalar Docker Engine e Compose

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 6.5 Verificar instalação

```bash
sudo docker run hello-world
# Deve exibir a mensagem de boas-vindas do Docker
```

### 6.6 Permitir que o usuário deploy use Docker sem sudo

```bash
sudo usermod -aG docker deploy
```

> ⚠️ **Saia da sessão e entre novamente** para aplicar:
> ```bash
> exit
> ssh deploy@<IP_DO_DROPLET>
> ```

### 6.7 Verificar se funciona sem sudo

```bash
docker --version
# Docker version 27.x.x, build xxxxxxx

docker compose version
# Docker Compose version v2.x.x
```

---

## 7. Clonando o Repositório e Configurando Variáveis

### 7.1 Clonar o projeto

```bash
cd /home/deploy
git clone https://github.com/seu-usuario/pyorganiza.git
cd pyorganiza
```

### 7.2 Criar o arquivo .env.prod

```bash
nano /home/deploy/pyorganiza/.env.prod
```

Conteúdo:

```ini
# ============================================
# Django
# ============================================
SECRET_KEY=d%#k9$2&x@m!q#p8v7n6b5$4r3t2y1u0i9o8i7u6y5t4r3e2w1q
DEBUG=False
ALLOWED_HOSTS=pyorganiza.seudominio.com,www.pyorganiza.seudominio.com,142.93.xxx.xxx

# ============================================
# PostgreSQL
# ============================================
DATABASE_NAME=pyorganiza
DATABASE_USER=pyorganiza_user
DATABASE_PASSWORD=#K9mP2xL8@jR5vN3qW7bZ!tY4fE6sH1c
```

> **Atenção:**
> - `SECRET_KEY` — Use a chave gerada no passo 2.2
> - `ALLOWED_HOSTS` — Inclua domínio(s) **e** IP do droplet, separados por vírgula
> - `DATABASE_PASSWORD` — Gere uma senha forte (ex: `openssl rand -base64 32`)
> - `DATABASE_ENGINE`, `DATABASE_HOST`, `DATABASE_PORT` são definidos no `docker-compose.yml`

### 7.3 Proteger o arquivo

```bash
chmod 600 /home/deploy/pyorganiza/.env.prod
```

**Nunca** commite este arquivo no Git.

### 7.4 Criar diretório para arquivos de mídia

```bash
mkdir -p /home/deploy/pyorganiza/media
```

---

## 8. Configurando Nginx e SSL com Let's Encrypt

### 8.1 Editar o server_name no nginx.conf

```bash
nano /home/deploy/pyorganiza/nginx/nginx.conf
```

Substitua `seu-dominio.com` pelo seu domínio real (ex: `pyorganiza.seudominio.com`).

### 8.2 Gerar certificado SSL com Let's Encrypt

> ⚠️ **Pré-requisito:** O domínio deve estar apontado para o IP do droplet (passo 3.5).

```bash
# Instalar certbot
sudo apt install -y certbot
```

Gerar certificado (modo standalone — porta 80 precisa estar livre):

```bash
sudo certbot certonly --standalone -d pyorganiza.seudominio.com -d www.pyorganiza.seudominio.com
```

> Se houver erro de porta ocupada, pare qualquer serviço na porta 80:
> ```bash
> sudo lsof -i :80
> sudo systemctl stop nginx  # se estiver rodando
> ```

Os certificados serão salvos em:
```
/etc/letsencrypt/live/pyorganiza.seudominio.com/fullchain.pem
/etc/letsencrypt/live/pyorganiza.seudominio.com/privkey.pem
```

### 8.3 Configurar permissões dos certificados

O Nginx no Docker precisa ler os certificados. Crie um diretório para copiá-los:

```bash
sudo mkdir -p /etc/ssl/pyorganiza
sudo cp /etc/letsencrypt/live/pyorganiza.seudominio.com/fullchain.pem /etc/ssl/pyorganiza/
sudo cp /etc/letsencrypt/live/pyorganiza.seudominio.com/privkey.pem /etc/ssl/pyorganiza/
sudo chmod 755 /etc/ssl/pyorganiza
sudo chmod 644 /etc/ssl/pyorganiza/fullchain.pem
sudo chmod 600 /etc/ssl/pyorganiza/privkey.pem
```

> **Alternativa:** Montar o diretório do Let's Encrypt diretamente no container (ver passo 8.5).

### 8.4 Configurar nginx.conf com SSL

Substitua o conteúdo de `nginx/nginx.conf`:

```nginx
upstream pyorganiza {
    server app:8000;
}

server {
    listen 80;
    server_name pyorganiza.seudominio.com www.pyorganiza.seudominio.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name pyorganiza.seudominio.com www.pyorganiza.seudominio.com;

    ssl_certificate /etc/ssl/pyorganiza/fullchain.pem;
    ssl_certificate_key /etc/ssl/pyorganiza/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # HSTS (força HTTPS nos navegadores)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /app/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://pyorganiza;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### 8.5 Montar certificados no docker-compose (opcional)

Se preferir montar os certificados diretamente do Let's Encrypt sem copiar, adicione ao serviço `nginx` no `docker-compose.yml`:

```yaml
  nginx:
    ...
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
      # Adicionar:
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - /var/www/certbot:/var/www/certbot
```

Ajuste o `nginx.conf` para usar os caminhos do Let's Encrypt:

```nginx
ssl_certificate /etc/letsencrypt/live/pyorganiza.seudominio.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/pyorganiza.seudominio.com/privkey.pem;
```

### 8.6 Auto-renovação do certificado SSL

O Let's Encrypt expira a cada 90 dias. Configure renovação automática:

```bash
sudo crontab -e
```

Adicione a linha:

```cron
0 3 * * * /usr/bin/certbot renew --quiet --post-hook "docker compose -f /home/deploy/pyorganiza/docker-compose.yml restart nginx"
```

> Se usou o volume mount do Let's Encrypt, o post-hook não precisa copiar nada.

---

## 9. Fazendo o Deploy dos Containers

### 9.1 Construir e iniciar

```bash
cd /home/deploy/pyorganiza
docker compose up -d --build
```

**O que acontece:**
1. **`db`** — PostgreSQL 16 Alpine inicia e cria o banco `pyorganiza`
2. **`app`** — Django sobe, roda `migrate`, `collectstatic` e inicia o Gunicorn
3. **`nginx`** — Nginx configura o reverse proxy e serve arquivos estáticos

### 9.2 Verificar status

```bash
docker compose ps
```

Saída esperada:
```
NAME               IMAGE              COMMAND                  SERVICE    STATUS        PORTS
pyorganiza_app     pyorganiza-app     "gunicorn core.wsgi…"    app        running       8000/tcp
pyorganiza_db      postgres:16-alpine "docker-entrypoint.s…"   db         running       5432/tcp
pyorganiza_nginx   nginx:1.27-alpine  "nginx -g 'daemon of…"   nginx      running       0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

### 9.3 Verificar logs

```bash
# Acompanhar todos os logs
docker compose logs -f

# Logs específicos
docker compose logs -f app
docker compose logs -f nginx
docker compose logs -f db
```

Aguarde até ver no log do app:
```
Starting gunicorn 25.0.3
Listening at: http://0.0.0.0:8000
```

### 9.4 Testar o acesso

Abra no navegador:
```
http://<IP_DO_DROPLET>
```

Se configurou DNS:
```
https://pyorganiza.seudominio.com
```

### 9.5 Resolver problemas de permissão de mídia (se necessário)

```bash
# O container roda como root dentro, mas se houver problema:
docker compose exec app chmod -R 755 /app/media
```

---

## 10. Pós-Deploy

### 10.1 Criar superusuário

```bash
docker compose exec app python manage.py createsuperuser
```

Preencha:
- **Username:** admin
- **Email:** admin@exemplo.com
- **Password:** (senha forte)

### 10.2 Carregar dados iniciais (categorias financeiras)

```bash
docker compose exec app python manage.py loaddata apps/finance/fixtures/category.json
```

> **Nota sobre a fixture:** O arquivo `category.json` está vinculado ao `user_id=1`. Execute o `loaddata` **após** criar o primeiro usuário, ou edite a fixture para associar corretamente.

### 10.3 Verificar no navegador

Acesse: `https://pyorganiza.seudominio.com/admin/` e faça login.

### 10.4 Ajustar permissão dos arquivos

```bash
# Garantir que o Nginx consiga ler os arquivos estáticos
docker compose exec app chmod -R 755 /app/staticfiles
```

---

## 11. Comandos de Manutenção

### 11.1 Gerenciamento dos containers

| Comando | Descrição |
|---------|-----------|
| `docker compose ps` | Status de todos os serviços |
| `docker compose logs -f app` | Logs da aplicação em tempo real |
| `docker compose logs -f nginx` | Logs do Nginx |
| `docker compose logs -f db` | Logs do PostgreSQL |
| `docker compose restart app` | Reiniciar apenas a aplicação |
| `docker compose restart nginx` | Reiniciar apenas o Nginx |
| `docker compose down` | Parar e remover containers (dados preservados) |
| `docker compose down -v` | ⚠️ Parar e **remover volumes** (destrói dados) |
| `docker compose up -d --build` | Reconstruir e reiniciar |
| `docker system prune -a` | Limpar imagens/containers não usados (liberar disco) |

### 11.2 Comandos Django

```bash
# Shell interativo do Django
docker compose exec app python manage.py shell

# Rodar migrations
docker compose exec app python manage.py migrate

# Coletar estáticos
docker compose exec app python manage.py collectstatic --noinput

# Criar superusuário
docker compose exec app python manage.py createsuperuser

# Acessar o banco via shell
docker compose exec app python manage.py dbshell
```

### 11.3 Acesso ao PostgreSQL

```bash
docker compose exec db psql -U pyorganiza_user -d pyorganiza
```

Dentro do psql:
```sql
\dt              -- listar tabelas
\d+ apps_finance_transaction  -- estrutura da tabela
SELECT * FROM auth_user;      -- consultar usuários
\q                -- sair
```

### 11.4 Acesso ao container da aplicação

```bash
docker compose exec app bash
```

---

## 12. Atualizando o Projeto

### 12.1 Passo a passo completo

```bash
cd /home/deploy/pyorganiza

# 1. Baixar as alterações do Git
git pull origin main

# 2. Reconstruir a imagem da aplicação (apenas o serviço app)
docker compose up -d --build app

# 3. Rodar novas migrations (se houver)
docker compose exec app python manage.py migrate --noinput

# 4. Coletar arquivos estáticos
docker compose exec app python manage.py collectstatic --noinput --clear

# 5. Reiniciar o Nginx para garantir que pegou novos estáticos
docker compose restart nginx
```

### 12.2 Script de atualização (deploy.sh)

Crie `/home/deploy/deploy.sh`:

```bash
#!/bin/bash
set -e

echo "=== Iniciando deploy do PyOrganiza ==="

cd /home/deploy/pyorganiza

echo "1. Atualizando código..."
git pull origin main

echo "2. Reconstruindo imagem da aplicação..."
docker compose up -d --build app

echo "3. Rodando migrations..."
docker compose exec -T app python manage.py migrate --noinput

echo "4. Coletando arquivos estáticos..."
docker compose exec -T app python manage.py collectstatic --noinput --clear

echo "5. Reiniciando Nginx..."
docker compose restart nginx

echo "=== Deploy concluído com sucesso! ==="
```

```bash
chmod +x /home/deploy/deploy.sh
```

Uso:

```bash
./deploy.sh
```

---

## 13. Backup e Restauração

### 13.1 Backup do banco de dados

```bash
# Criar diretório de backups
mkdir -p /home/deploy/backups

# Backup manual
docker compose exec -T db pg_dump -U pyorganiza_user pyorganiza | gzip > /home/deploy/backups/pyorganiza_$(date +%Y%m%d_%H%M%S).sql.gz
```

### 13.2 Backup dos arquivos de mídia

```bash
# Backup do volume de mídia
tar -czf /home/deploy/backups/media_$(date +%Y%m%d).tar.gz -C /home/deploy/pyorganiza/media .
```

### 13.3 Script de backup automatizado

Crie `/home/deploy/backup.sh`:

```bash
#!/bin/bash
set -e

BACKUP_DIR=/home/deploy/backups
PROJECT_DIR=/home/deploy/pyorganiza
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

mkdir -p $BACKUP_DIR

echo "=== Iniciando backup em $DATE ==="

# Backup do banco
echo "Backup do PostgreSQL..."
cd $PROJECT_DIR
docker compose exec -T db pg_dump -U pyorganiza_user pyorganiza | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup dos arquivos de mídia
echo "Backup dos arquivos de mídia..."
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C $PROJECT_DIR media

# Remover backups antigos
echo "Removendo backups com mais de $RETENTION_DAYS dias..."
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "=== Backup concluído! ==="
echo "Arquivos em: $BACKUP_DIR"
ls -lh $BACKUP_DIR
```

```bash
chmod +x /home/deploy/backup.sh
```

Agendar no cron (executa todos os dias às 02:00):

```bash
crontab -e
```

Adicione:

```cron
0 2 * * * /home/deploy/backup.sh >> /home/deploy/backups/backup.log 2>&1
```

### 13.4 Restauração do banco

```bash
# 1. Descomprimir o backup
gunzip -c /home/deploy/backups/db_20260703_020000.sql.gz > /tmp/restore.sql

# 2. Copiar para dentro do container
docker compose cp /tmp/restore.sql db:/tmp/restore.sql

# 3. Restaurar
docker compose exec db psql -U pyorganiza_user -d pyorganiza -f /tmp/restore.sql

# 4. Limpar
rm /tmp/restore.sql
```

### 13.5 Restauração completa (do zero)

Se precisar recriar tudo a partir do backup:

```bash
cd /home/deploy/pyorganiza

# Parar containers
docker compose down

# Remover volume do banco (⚠️ destrói dados atuais)
docker volume rm pyorganiza_postgres_data || true

# Subir apenas o banco
docker compose up -d db
sleep 10  # aguardar PostgreSQL iniciar

# Restaurar o banco
gunzip -c /home/deploy/backups/db_20260703_020000.sql.gz | docker compose exec -T db psql -U pyorganiza_user -d pyorganiza

# Restaurar mídia
tar -xzf /home/deploy/backups/media_20260703.tar.gz -C /home/deploy/pyorganiza/

# Subir todos os serviços
docker compose up -d
```

---

## 14. Monitoramento

### 14.1 Comandos básicos

```bash
# Uso de recursos
docker stats --no-stream

# Espaço em disco
df -h

# Memória e swap
free -h

# Processos
htop  # ou top
```

### 14.2 Logs centralizados

```bash
# Últimos 50 logs do app
docker compose logs --tail=50 app

# Logs em tempo filtrado por erro
docker compose logs -f app | grep -i error

# Logs do Nginx (requisições)
docker compose logs -f nginx
```

### 14.3 Verificar saúde da aplicação

```bash
# Testar se o app responde
curl -I http://localhost:8000/admin/

# Verificar healthcheck (se configurado)
```

### 14.4 Notificações de erro

Configure o Django para enviar e-mails de erro (opcional):

No `.env.prod`:
```ini
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
DEFAULT_FROM_EMAIL=seu-email@gmail.com
SERVER_EMAIL=seu-email@gmail.com
ADMINS=Seu Nome,seu-email@gmail.com
```

No `settings.py` (adicione):
```python
if not DEBUG:
    ADMINS = [("Admin", "seu-email@gmail.com")]
    MANAGERS = ADMINS
```

---

## 15. Rollback

### 15.1 Rollback para versão anterior do código

```bash
cd /home/deploy/pyorganiza

# Ver histórico de commits
git log --oneline -10

# Voltar para um commit específico
git checkout <hash-do-commit-anterior>

# Reconstruir e reiniciar
docker compose up -d --build app
```

### 15.2 Rollback do banco de dados

```bash
# Restaurar backup anterior (ver seção 13.4)
gunzip -c /home/deploy/backups/db_20260702_020000.sql.gz | docker compose exec -T db psql -U pyorganiza_user -d pyorganiza
```

### 15.3 Rollback completo (código + banco)

```bash
# 1. Voltar o código
git checkout <hash-anterior>

# 2. Restaurar o banco
gunzip -c /home/deploy/backups/db_*.sql.gz | docker compose exec -T db psql -U pyorganiza_user -d pyorganiza

# 3. Reconstruir e subir
docker compose up -d --build
```

---

## 16. Troubleshooting

### 16.1 Erro 502 Bad Gateway

Nginx não consegue se conectar ao app.

```bash
# Verificar se o app está rodando
docker compose ps app

# Ver logs do app
docker compose logs app

# Causas comuns:
# - App demorou para iniciar → reiniciar nginx
docker compose restart nginx

# - App crashou → ver logs detalhados
docker compose logs app --tail=50

# - Gunicorn sem workers disponíveis → aumentar workers no docker-compose.yml
# command: gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 5
```

### 16.2 Erro de memória (WeasyPrint)

A geração de PDF falha com `Killed` ou `exit code 137`.

```bash
# Verificar uso de memória
docker stats --no-stream

# Verificar se o swap está ativo
free -h

# Soluções:
# 1. Aumentar swap (se não fez no passo 4.8)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 2. Limitar memória do container no docker-compose.yml:
# app:
#   deploy:
#     resources:
#       limits:
#         memory: 3g
#       reservations:
#         memory: 1g

# 3. Upgrade do droplet para 8 GB (recomendado se for usar PDF intensamente)
```

### 16.3 Erro: "Invalid HTTP_HOST header"

O Django está recebendo requisição de um host não listado no `ALLOWED_HOSTS`.

```bash
# Verificar ALLOWED_HOSTS
nano /home/deploy/pyorganiza/.env.prod

# Deve conter domínio e IP:
ALLOWED_HOSTS=pyorganiza.seudominio.com,www.pyorganiza.seudominio.com,142.93.xxx.xxx

# Aplicar alteração (reconstruir é necessário para pegar novo .env)
docker compose down
docker compose up -d --build
```

### 16.4 Erro: "Database does not exist"

```bash
# Verificar logs do db
docker compose logs db

# Criar o banco manualmente
docker compose exec db psql -U pyorganiza_user -c "CREATE DATABASE pyorganiza;"

# Ou recriar do zero (⚠️ destrói dados)
docker compose down -v
docker compose up -d
```

### 16.5 Erro de conexão com o banco (app não sobe)

```bash
# Verificar se o banco está pronto
docker compose logs db | grep "ready to accept connections"

# Testar conexão
docker compose exec db pg_isready -U pyorganiza_user

# Verificar credenciais no .env.prod
# O docker-compose.yml passa POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
# O .env.prod deve ter DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD iguais
```

### 16.6 Erro: Permission denied ao escrever em /app/media

```bash
# O container roda como root, mas se houver problema:
docker compose exec app chown -R 1000:1000 /app/media
docker compose exec app chmod -R 755 /app/media
```

### 16.7 Erro no collectstatic durante build

```bash
# Verificar se os arquivos estáticos existem
ls -la /home/deploy/pyorganiza/static/

# Build manual ignorando o collectstatic no Dockerfile se necessário
# Comente a linha RUN collectstatic no Dockerfile.
# Depois execute manualmente:
docker compose exec app python manage.py collectstatic --noinput
```

### 16.8 Erro: "No such file or directory" no nginx.conf

```bash
# Verificar se o arquivo existe
ls -la /home/deploy/pyorganiza/nginx/nginx.conf

# Verificar sintaxe do nginx.conf
docker compose exec nginx nginx -t
```

### 16.9 Docker: "no space left on device"

```bash
# Verificar espaço
df -h

# Limpar imagens e containers não usados
docker system prune -a -f

# Verificar logs dos containers (podem estar gigantes)
docker compose logs --tail=100 app > /dev/null  # truncar se necessário
```

---

## 17. Referências

- [DigitalOcean Droplets Documentation](https://docs.digitalocean.com/products/droplets/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Let's Encrypt / Certbot](https://certbot.eff.org/)
- [WeasyPrint Installation](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#ubuntu)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/16/index.html)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Fail2ban Documentation](https://www.fail2ban.org/wiki/index.php/MANUAL_0_8)
- [Gunicorn Settings](https://docs.gunicorn.org/en/stable/settings.html)

---

> **Dica final:** Sempre teste o deploy em um droplet de baixo custo antes de ir para produção. Mantenha backups regulares e monitore os logs nos primeiros dias após o deploy.
