# Автоматизированное развёртывание проекта Reviews

- [Настройка контроллера](#настройка-контроллера)
- [Подготовка сервера-ноды](#подготовка-сервера-ноды)
- [Работа с Ansible](#работа-с-ansible)
  - [Подготовка и проверка](#подготовка-и-проверка)
  - [Развертывание](#развертывание)
    - [Bootstrap серверов](#bootstrap-серверов)
    - [Деплой Nginx](#деплой-nginx)
    - [Деплой Backend](#деплой-backend)
- [Архитектура](#архитектура)
- [Безопасность](#безопасность)



# Настройка контроллера

> Тестировалось на Ubuntu WSL.

1. Генерация SSH-ключа:
```bash
ssh-keygen -t ed25519
```
2. Установка Ansible в виртуальное окружение (venv):
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip
python3 -m venv ~/ansible-env
source ~/ansible-env/bin/activate
pip install -U pip
pip install ansible
ansible --version
```



# Подготовка сервера-ноды

> Тестировалось на VPS Debian 12.

1. Настройка SSH-доступа по ключу на удалённом сервере:
```bash
ssh-copy-id deploy@192.168.56.X
```
2. Создание A-записи в DNS для домена хоста.
3. Проверка корректности адресов в инвентаре `inventory/prod/hosts.ini`.



# Работа с Ansible

## Подготовка и проверка

1. Активация виртуального окружения:
```bash
source ~/ansible-env/bin/activate
```
2. Создание конфигурационных файлов из шаблонов:
```bash
cp inventory/prod/group_vars/all.example.yml inventory/prod/group_vars/all.yml
cp inventory/prod/hosts.example.ini inventory/prod/hosts.ini
```
3. Заполнение переменных: отредактируйте `inventory/prod/group_vars/all.yml`, указав реальные секреты и домены.

4. Проверка доступности хостов:
```bash
ansible all -m ping
```

## Развертывание

Полный запуск всех этапов развёртывания:
```bash
ansible-playbook playbooks/deploy-full.yml
```

### Bootstrap серверов

Подготовка базового окружения на целевых хостах:
```bash
ansible-playbook playbooks/bootstrap.yml
```

**Что делает playbook:**
- Устанавливает системные зависимости (`acl`, `ca-certificates`, `curl`)
- Настраивает официальный репозиторий Docker
- Устанавливает Docker Engine и плагин Docker Compose
- Запускает и включает службу Docker
- Добавляет указанных пользователей в группу `docker`

Пример конфигурации (`group_vars/all.yml`):
```yaml
docker_users:
  - deploy
```

### Деплой Nginx

Настройка веб-сервера и получение SSL-сертификатов:
```bash
ansible-playbook playbooks/deploy-nginx.yml
```

**Что делает playbook:**
- Устанавливает Nginx и Certbot
- Создаёт директорию для ACME-челленджа Certbot (`/var/www/certbot`)
- Генерирует и валидирует виртуальный хост Nginx
- Выпускает SSL-сертификат Let's Encrypt через Certbot
- Настраивает автоматическую перезагрузку Nginx при продлении сертификата

Пример конфигурации (`group_vars/all.yml`):
```yaml
# Nginx config
domain_name: reviews.work.gd

# Certbot config
enable_https: true
letsencrypt_email: example@mail.com

# Backend port for proxying
backend_port: 8000
```

### Деплой Backend

Развёртывание приложения и его зависимостей:
```bash
ansible-playbook playbooks/deploy-backend.yml
```

**Что делает playbook:**
- Создаёт рабочую директорию `/opt/reviews`
- Генерирует и загружает `docker-compose.yml` и `.env` из шаблонов
- Выполняет авторизацию в GHCR (GitHub Container Registry)
- Подтягивает контейнеры и запускает сервис через `docker compose`

Пример конфигурации (`group_vars/all.yml`):
```yaml
# GHCR credentials
ghcr_username: OneTwoZzzPlus
ghcr_token: "ChangeMe"

# Backend
backend_image: ghcr.io/onetwozzzplus/reviews-backend:latest
backend_port: 8000

backend_log_level: INFO
backend_pg_echo: false
backend_auth_verify: true

# Database
pg_host: localhost
pg_port: 5432
pg_database: reviews
pg_username: admin
pg_password: "ChangeMe"

# Grafana
grafana_password: "ChangeMe"
```



# Архитектура

**Стек сервисов:**
```text
Internet -> Nginx + Certbot -> Backend API -> PostgreSQL
```

**Мониторинг:**
```text
Grafana <- Prometheus <- Backend
```



# Безопасность

В Git-репозиторий **НЕ должны** попадать:
- `.env`
- `inventory/*/group_vars/all.yml`
- `inventory/*/hosts.ini`
- Приватные SSH-ключи
- Токены доступа к Registry
- Production-секреты и пароли

Для работы используйте шаблоны:
- `all.example.yml`
- `hosts.example.ini`

**Рекомендации по безопасности сервера:**
- Использовать отдельного `deploy`-пользователя с ограниченными `sudo`-правами
- Отключить авторизацию по паролю и вход под `root` по SSH
- Ограничить сетевой доступ с помощью Firewall (открыты только порты `22`, `80`, `443`)