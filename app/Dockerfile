FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

# Usuario sin privilegios (mínimo privilegio, como vimos en Ciberseguridad)
RUN useradd --uid 10001 --no-create-home appuser
USER 10001

EXPOSE 8080
# Un solo proceso con varios hilos: con varios procesos, cada uno tendría
# sus propios contadores y /metrics devolvería solo los de uno de ellos.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", \
     "--log-level", "warning", "app:app"]
