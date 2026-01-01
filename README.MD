# Типичные сценарии запуска

### Тестирование
Неободимо поместить в env все переменные.
```bash
uvicorn src.main:app --reload --env-file .env.dev
```


### CI/CD (боевой запуск)
Необходимо поднять окружение и stateful сервисы: ***пока что скрытая инфа***.

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