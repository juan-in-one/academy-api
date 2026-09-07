FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Usuario sin privilegios (UID/GID 10001, coincide a propósito con el
# securityContext del chart de Helm, que exige > 10000) en vez de correr como
# root, que es el valor por defecto si no se especifica ningún USER.
# Ver Trivy DS-0002.
RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app
USER 10001:10001

EXPOSE 8000

# Ver Trivy DS-0026. Usa Python en vez de curl: la imagen "slim" no trae curl
# instalado, y añadirlo solo para esto aumentaría la imagen sin necesidad.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
