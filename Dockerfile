# ── road_damage_app/Dockerfile ──
FROM python:3.11-slim

# system libs needed by WeasyPrint + build tools
RUN apt-get update && apt-get install -y \
        build-essential \
        libffi-dev \
        libcairo2 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libgdk-pixbuf2.0-0 \
        libjpeg-turbo-progs \
        fonts-liberation      \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# —— Python deps ————————————————————
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# —— App code ————————————————————————
COPY backend /app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

