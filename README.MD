# Типичные сценарии запуска

### Тестирование
Неободимо поместить в env все переменные.
```bash
uvicorn src.main:app --reload --env-file .env.dev
```


### CI/CD
Неободимо поместить переменные и auth данные в GitHub `Settings` -> `Secrets`.
```bash
git add .
git commit -m "Fixing GA"
git push -u origin main
```
