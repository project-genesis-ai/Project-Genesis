FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY requirements-persistence.txt ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
COPY web ./web
COPY start.sh ./start.sh

RUN ln -s /app/web /usr/local/lib/python3.12/web \
    && python -m pip install --upgrade pip \
    && python -m pip install -r requirements-persistence.txt \
    && python -m pip install .

EXPOSE 10000

CMD ["sh", "./start.sh"]
