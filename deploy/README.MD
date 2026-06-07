# Автоматизированное развёртывание проекта Reviews

- [Архитектура](#архитектура)
- [Структура репозитория](#структура-репозитория)
  - [Распределение ответственности](#распределение-ответственности)
  - [Окружения Ansible](#окружения-ansible)
- [Настройка контроллера](#настройка-контроллера)
- [Подготовка нодов](#подготовка-нодов)
  - [Настройка VM](#настройка-нодов-vm-тестовый-стенд)
  - [Настройка боевых нодов](#настройка-боевых-нодов)
- [Работа с Ansible](#работа-с-ansible)
  - [Bootstrap](#bootstrap-серверов)
  - [Persistent сервисы](#деплой-persistent-сервисов)
  - [Backend](#деплой-backend-сервисов)
  - [Nginx](#деплой-nginx)
  - [HTTPS](#https)
  - [Docker Registry](#docker-registry-опционально)
- [Безопасность](#безопасность)
- [Управление](#управление)
- [CI/CD Pipeline](#cicd-pipeline)
- [Roadmap](#roadmap)
- [Manual deployment (legacy)](#manual-deployment-legacy)

# Архитектура

**Service stack:**
```text
Internet -> Nginx + CertBot -> Backend API -> PostgreSQL
```
**Monitoring:**
```text
Grafana <- Prometheus <- Backend 
```

# Структура репозитория

```bash
deploy/
├── ansible/    # Ansible automation
├── compose/    # Docker Compose stacks
├── .env        # Секреты и deployment variables
└── README.md
```

## Распределение ответственности

| Compose | Ansible |
| --- | --- |
| контейнеры и сети | bootstrap серверов |
| volumes и environment | установка Docker и зависимостей |
| сервисы backend/database | деплой compose файлов |
| monitoring stack | настройка Nginx и HTTPS |
| runtime конфигурация | orchestration и provisioning |

## Окружения Ansible

```bash
ansible/inventory
├── dev    # тестовый стенд [default]
│   ├── group_vars
│   │   ├── all.yml
│   │   └── all.yml.example
│   └── hosts.ini
└── prod   # боевое окружение
    ├── group_vars
    │   ├── all.yml
    │   └── all.yml.example
    └── hosts.ini
```

# Настройка контроллера

> Тестировалось на Ubuntu WSL

## Установка Ansible venv

```bash
ssh-keygen -t ed25519 # Генерация SSH ключа

sudo apt install -y python3-venv python3-pip

python3 -m venv ~/ansible-env

source ~/ansible-env/bin/activate

pip install -U pip
pip install ansible

ansible --version
```

# Подготовка нодов

> Тестировалось на Ubuntu в VirtualBox и на VPS

## Настройка нодов VM (тестовый стенд)

1) Устанавливаем Ubuntu на одну VM и клонируем.

Настраиваем сеть на клонированных VM:

```bash
sudo hostnamectl set-hostname ansN

sudo rm -f /etc/machine-id
sudo systemd-machine-id-setup

sudo cloud-init clean

sudo reboot
```

> Используем inventory `inventory/dev/hosts.ini` (по умолчанию).

## Настройка боевых нодов

1) Подготавливаем VPS или любую Linux-машину с SSH доступом.

> Используем inventory `inventory/prod/hosts.ini`.

## Общие настройки

### Создание deploy пользователя

На нодах:

```bash
sudo adduser deploy

sudo usermod -aG sudo deploy

sudo visudo
```

Добавить:

```text
deploy ALL=(ALL) NOPASSWD:ALL
```

### Добавление SSH ключей

На контроллере:

```bash
ssh-copy-id deploy@192.168.56.X
```

# Работа с Ansible

## Активация окружения

```bash
source ~/ansible-env/bin/activate

cd ansible
```

## Проверка доступности серверов

```bash
ansible all -m ping
```

## Bootstrap серверов

Устанавливает:

- Docker Engine
- Docker Compose Plugin
- базовые зависимости

```bash
ansible-playbook playbooks/bootstrap.yml
```

## Деплой persistent сервисов

Разворачивает:

- PostgreSQL
- Prometheus
- Grafana

```bash
ansible-playbook playbooks/deploy-persistent.yml
```

## Деплой backend сервисов

Разворачивает:

- backend compose stack
- обновление образов
- авторизация в registry (опционально)

```bash
ansible-playbook playbooks/deploy-backend.yml
```

## Деплой nginx

Разворачивает:

- Nginx reverse proxy
- HTTPS через CertBot (опционально)

```bash
ansible-playbook playbooks/deploy-nginx.yml
```

## HTTPS

HTTPS управляется через inventory variables.

Пример:

```yaml
enable_https: true
domain_name: api.example.com
letsencrypt_email: admin@example.com
```

Требования:

- белый IP
- открытые 80/443 порты
- DNS запись

## Docker Registry (опционально)

> Для публичных образов можно оставить пустым.

Поддерживается:

- Docker Hub
- GHCR

Пример:

```yaml
docker_registry_url: ghcr.io
docker_registry_username: myuser
docker_registry_password: mytoken
```

# Безопасность

В репозиторий НЕ должны попадать:

- `.env`
- `inventory/*/group_vars/all.yml`
- приватные SSH ключи
- токены registry
- production secrets

Используйте:

- `.env.example`
- `all.yml.example`

Рекомендуется:

- использовать отдельного deploy пользователя
- отключить root login по SSH
- использовать SSH keys вместо password auth
- ограничить firewall (80/443/22)

# Управление

## Перезапуск persistent сервисов

```bash
cd /opt/reviews/persistent/

docker compose up -d
```

## Обновление backend

```bash
cd /opt/reviews/backend/

docker compose pull backend

docker compose up -d --no-deps backend
```

# CI/CD Pipeline

```text
git push
    ↓
GitHub Actions
    ↓
docker build
    ↓
docker push
    ↓
ansible deploy
    ↓
docker compose pull
    ↓
docker compose up -d
```

# Roadmap

- [x] Docker Compose deployment
- [x] Ansible provisioning
- [x] HTTPS + Nginx
- [x] Monitoring
- [ ] Database migrations
- [ ] Zero-downtime deploy
- [ ] Blue/Green deploy
- [ ] Multi-node scaling
- [ ] Kubernetes manifests
- [ ] Helm charts