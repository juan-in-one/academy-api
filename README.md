# academy-api

Microservicio de la plataforma [juan-in-one](https://github.com/juan-in-one) — certificaciones profesionales
(conseguidas y objetivo) y seguimiento diario de objetivos de aprendizaje (ej. inglés, tiempo dedicado a
proyectos personales).

Parte del stack de aprendizaje DevOps/DevSecOps/GitOps: Kubernetes + Helm + GitHub Actions (CI) + ArgoCD (CD)
sobre un clúster local en OrbStack. Observabilidad completa (métricas, logs, trazas) vía OpenTelemetry +
Prometheus/Loki/Tempo — mismo patrón que el resto de microservicios de la plataforma.

Stack: Python + FastAPI + SQLAlchemy (async) + Postgres

## Desarrollo local

```bash
cp .env.example .env
docker compose up --build
```

API disponible en `http://localhost:8002` (docs interactivas en `/docs`).

## Endpoints

- `GET /health`
- `POST /certifications` / `GET /certifications` / `GET /certifications/{id}` / `DELETE /certifications/{id}`
- `POST /goals` / `GET /goals` / `GET /goals/{id}` / `DELETE /goals/{id}`
- `POST /goals/{goal_id}/check-ins` — crea o actualiza el check-in del día indicado (un check-in por objetivo
  y día; volver a marcar el mismo día actualiza los minutos en vez de duplicar)
- `GET /goals/{goal_id}/check-ins`
- `GET /goals/{goal_id}/today` — ¿ya he marcado el objetivo de hoy?, y si lo he cumplido o no

## Modelo de datos

- **`Certification`**: `status` (`completed` / `in_progress` / `planned`), fechas de obtención/objetivo.
- **`Goal`**: un objetivo diario configurable (nombre + minutos objetivo), ej. "Inglés" → 30 min/día.
- **`GoalCheckIn`**: registro diario de minutos dedicados a un objetivo — la ausencia de check-in para un día
  es justo lo que distingue "no lo he marcado" de "lo marqué pero no llegué al tiempo".
