# [Reviews](https://onetwozzzplus.github.io/reviews/#/) - отзывы на преподавателей

> Понравился проект? Не забудь поставить ⭐ на репозитории.

[![Frontend Repository](https://img.shields.io/badge/Frontend-24292E?style=for-the-badge&logo=github&logoColor=white)](https://github.com/OneTwoZzzPlus/reviews)
[![Backend Repository](https://img.shields.io/badge/Backend-24292E?style=for-the-badge&logo=github&logoColor=white)](https://github.com/OneTwoZzzPlus/reviews-backend)

## Стек

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![SQLAdmin](https://img.shields.io/badge/SQLAdmin-000000?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)

![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Compose-1D63ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![Ansible](https://img.shields.io/badge/Ansible-EE0000?style=for-the-badge&logo=ansible&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)
![CertBot](https://img.shields.io/badge/CertBot-003A70?style=for-the-badge&logo=letsencrypt&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)

## Тестирование

```bash
make dev
```

<details>
<summary>Альтернативно</summary>

```bash
fastapi dev src\main.py
```

```bash
uvicorn main:app --reload --app-dir src
```

</details>

## Линтинг и тесты

```bash
make lint
make test
```

<details>
<summary>Альтернативно</summary>

```bash
ruff check --fix .
pytest tests/ -v
```

</details>

## Развертывание

**[Иструкция по развертыванию через Ansible.](./deploy/README.MD)**

<details>
<summary> Ручное развертывание (legacy) </summary>

1. Добавить в директорию `/opt/reviews` настроенные [compose файлы](/deploy/roles/backend/templates/):

```bash
/opt/reviews
├── .env
├── docker-compose.yml
└── prometheus.yml
```

2. Запустить backend:

```bash
docker compose -f /opt/reviews/docker-compose.yml up -d
```

3. Настроить nginx заполненным [конфигом](/deploy/roles/nginx/templates/nginx.conf.j2)

</details>

## CI/CD

### [CI Pipeline](.github/workflows/ci.yml)

> Автоматически срабатывает при каждом push и pull_request

- Устанавливает окружение Python 3.11, проверяет код с помощью Ruff и прогоняет тесты через Pytest.

- При изменениях в ветке main собирает Docker-образ с помощью Buildx и пушит его в GitHub Container Registry (ghcr.io) с тегами latest и короткой строкой sha-commit.

### [CD Deploy](.github/workflows/cd.yml)

> Автоматически запускается после успешного завершения пайплайна CI Pipeline в ветке main (также возможен ручной запуск через workflow_dispatch)

- Авторизуется на целевом сервере по SSH.

- Выполняет `docker login` в GHCR.

- Подтягивает свежий образ бэкенда (`docker compose pull backend`).

- Перезапускает контейнер без простоя других сервисов (`docker compose up -d --no-deps backend`).

- Очищает старые неиспользуемые Docker-образы (`docker image prune -f`).

### Необходимые Secrets в GitHub

🔑 `Settings` $\rightarrow$ `Secrets and variables` $\rightarrow$ `Actions`

| Secret         | Описание                                        |
| -------------- | ----------------------------------------------- |
| GHCR_PAT       | Personal Access Token с правами `read:packages` |
| SERVER_HOST    | IP-адрес или доменное имя целевого сервера      |
| SERVER_USER    | Имя пользователя SSH для подключения к серверу  |
| SERVER_SSH_KEY | Приватный SSH-ключ для авторизации на сервере   |
