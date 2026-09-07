import uuid
from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import make_asgi_app
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import engine, get_db, init_db
from app.models import Certification, Goal, GoalCheckIn
from app.schemas import (
    CertificationCreate,
    CertificationOut,
    GoalCheckInCreate,
    GoalCheckInOut,
    GoalCreate,
    GoalOut,
    GoalTodayStatus,
)

app = FastAPI(title=settings.app_name)

# Identifica el servicio tanto en métricas como en trazas — mismo patrón que
# car-api/sport-api (ver wiki/log.md 2026-09-03/2026-09-07).
resource = Resource.create({"service.name": "academy-api"})

# Métricas (Fase B)
metrics.set_meter_provider(
    MeterProvider(metric_readers=[PrometheusMetricReader()], resource=resource)
)
meter = metrics.get_meter("academy-api")

# Trazas (Fase D) — push vía OTLP a Alloy, que reenvía a Tempo.
trace.set_tracer_provider(TracerProvider(resource=resource))
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint="alloy.monitoring.svc.cluster.local:4317", insecure=True)
    )
)

# excluded_urls: /health (sondas de Kubernetes) y /metrics (el propio
# Prometheus scrapeándose a sí mismo) no son tráfico de negocio real.
FastAPIInstrumentor.instrument_app(app, excluded_urls="/health,/metrics")

# Cada consulta a Postgres aparece como span hijo dentro de la traza HTTP.
SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

app.mount("/metrics", make_asgi_app())

goal_check_ins_created = meter.create_counter(
    name="academy_goal_check_ins_total",
    description="Check-ins de objetivos diarios registrados",
)


@app.on_event("startup")
async def on_startup() -> None:
    await init_db()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# --- Certificaciones ---------------------------------------------------


@app.post("/certifications", response_model=CertificationOut, status_code=201)
async def create_certification(
    payload: CertificationCreate, db: AsyncSession = Depends(get_db)
) -> Certification:
    certification = Certification(**payload.model_dump())
    db.add(certification)
    await db.commit()
    await db.refresh(certification)
    return certification


@app.get("/certifications", response_model=list[CertificationOut])
async def list_certifications(db: AsyncSession = Depends(get_db)) -> list[Certification]:
    result = await db.execute(select(Certification).order_by(Certification.created_at.desc()))
    return list(result.scalars().all())


@app.get("/certifications/{certification_id}", response_model=CertificationOut)
async def get_certification(
    certification_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> Certification:
    certification = await db.get(Certification, certification_id)
    if certification is None:
        raise HTTPException(status_code=404, detail="Certification not found")
    return certification


@app.delete("/certifications/{certification_id}", status_code=204)
async def delete_certification(
    certification_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> None:
    certification = await db.get(Certification, certification_id)
    if certification is None:
        raise HTTPException(status_code=404, detail="Certification not found")
    await db.delete(certification)
    await db.commit()


# --- Objetivos -----------------------------------------------------------


@app.post("/goals", response_model=GoalOut, status_code=201)
async def create_goal(payload: GoalCreate, db: AsyncSession = Depends(get_db)) -> Goal:
    goal = Goal(**payload.model_dump())
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


@app.get("/goals", response_model=list[GoalOut])
async def list_goals(db: AsyncSession = Depends(get_db)) -> list[Goal]:
    result = await db.execute(select(Goal).order_by(Goal.created_at))
    return list(result.scalars().all())


@app.get("/goals/{goal_id}", response_model=GoalOut)
async def get_goal(goal_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Goal:
    goal = await db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@app.delete("/goals/{goal_id}", status_code=204)
async def delete_goal(goal_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    goal = await db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    await db.delete(goal)
    await db.commit()


# --- Check-ins diarios -----------------------------------------------------


@app.post("/goals/{goal_id}/check-ins", response_model=GoalCheckInOut, status_code=201)
async def create_or_update_check_in(
    goal_id: uuid.UUID, payload: GoalCheckInCreate, db: AsyncSession = Depends(get_db)
) -> GoalCheckIn:
    """Crea el check-in de ese día, o actualiza los minutos si ya existía uno
    (un check-in por objetivo y día — ver la restricción única en el modelo).
    Permite volver a marcar el mismo día sin que falle por duplicado."""
    goal = await db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")

    result = await db.execute(
        select(GoalCheckIn).where(GoalCheckIn.goal_id == goal_id, GoalCheckIn.date == payload.date)
    )
    check_in = result.scalar_one_or_none()
    if check_in is None:
        check_in = GoalCheckIn(goal_id=goal_id, **payload.model_dump())
        db.add(check_in)
    else:
        check_in.minutes = payload.minutes
        check_in.notes = payload.notes

    await db.commit()
    await db.refresh(check_in)
    goal_check_ins_created.add(1)
    return check_in


@app.get("/goals/{goal_id}/check-ins", response_model=list[GoalCheckInOut])
async def list_check_ins(
    goal_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> list[GoalCheckIn]:
    result = await db.execute(
        select(GoalCheckIn).where(GoalCheckIn.goal_id == goal_id).order_by(GoalCheckIn.date.desc())
    )
    return list(result.scalars().all())


@app.get("/goals/{goal_id}/today", response_model=GoalTodayStatus)
async def get_today_status(
    goal_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> GoalTodayStatus:
    """Respuesta directa a "¿he marcado ya el objetivo de hoy?" — sin tener
    que mirar la lista de check-ins a mano cada vez."""
    goal = await db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")

    today = date.today()
    result = await db.execute(
        select(GoalCheckIn).where(GoalCheckIn.goal_id == goal_id, GoalCheckIn.date == today)
    )
    check_in = result.scalar_one_or_none()

    if check_in is None:
        return GoalTodayStatus(
            goal_id=goal.id,
            goal_name=goal.name,
            date=today,
            target_minutes=goal.target_minutes,
            checked_in=False,
        )
    return GoalTodayStatus(
        goal_id=goal.id,
        goal_name=goal.name,
        date=today,
        target_minutes=goal.target_minutes,
        checked_in=True,
        minutes=check_in.minutes,
        goal_met=check_in.minutes >= goal.target_minutes,
    )
