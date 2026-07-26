# [Reviews](https://onetwozzzplus.github.io/reviews/#/) - отзывы на преподавателей

[![Frontend Repository](https://img.shields.io/badge/Frontend-24292E?style=for-the-badge&logo=github&logoColor=white)](https://github.com/OneTwoZzzPlus/reviews)
[![Backend Repository](https://img.shields.io/badge/Backend-24292E?style=for-the-badge&logo=github&logoColor=white)](https://github.com/OneTwoZzzPlus/reviews-backend)

## Стек
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)
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
##### Неободимо поместить в `.env` все переменные.
```
LOG_LEVEL=INFO
PG_ECHO=FALSE
AUTH_VERIFY=FALSE

PG_HOST=localhost
PG_PORT=5432
PG_DATABASE=reviews
PG_USERNAME=admin
PG_PASSWORD=admin
```

##### Запустить локально
```bash
fastapi dev src\main.py
```
или
```bash
uvicorn main:app --reload --app-dir src
```

## Автоматическое развертывание

[Иструкция по развертыванию через Ansible.](./deploy/README.MD)

## Ручное развертывание (legacy)

### Зарегистрировать домен

Например, бесплатно тут:

- https://www.duckdns.org/
- https://dnsexit.com

### На хосте поднять окружение

1) Добавить в директорию `/opt/reviews` настроенные compose файлы из `compose/`:

```bash
/opt/reviews
├── backend
│   └── docker-compose.yml
└── persistent
    ├── docker-compose.yml
    └── prometheus.yml
```

2) Создать сеть:

```bash
docker network create reviews_network
```

3) Запустить persistent stack:

```bash
docker compose -f /opt/reviews/persistent/docker-compose.yml up -d
```

4) Запустить backend:

```bash
docker compose -f /opt/reviews/backend/docker-compose.yml up -d
```

### CI/CD

Неободимо поместить secret данные в GitHub `Settings` -> `Secrets`.
- DOCKER_USER
- DOCKER_TOKEN
- SERVER_HOST
- SERVER_USER
- SERVER_SSH_KEY

Workflow запуститься после `push` в `main`.
```bash
git add .
git commit -m "Fixing GA"
git push -u origin main
```