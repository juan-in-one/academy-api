FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# perl-base viene en la imagen base "slim" mismo, sin que la app lo use para
# nada (es Python puro) — Debian lo marca "essential" así que hay que forzar
# el borrado con --allow-remove-essential. Elimina de raíz 3 CVEs CRITICAL de
# Debian sin parche disponible (perl-base) en vez de dejarlas ahí para
# siempre: verificado que la imagen sigue arrancando y sirviendo tráfico
# igual sin él.
# DS-0017 exige que "update" vaya seguido de "install" en el mismo RUN (para
# evitar instalar versiones desincronizadas) pero aquí no se instala nada
# nuevo, solo se elimina un paquete: no aplica el riesgo que la regla
# intenta prevenir. La etiqueta de ignore tiene que ser el último comentario
# pegado al RUN, si no Trivy no la reconoce.
# trivy:ignore:DS-0017
RUN apt-get update \
    && apt-get remove --purge -y --allow-remove-essential perl-base \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

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
