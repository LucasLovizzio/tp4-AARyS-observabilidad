"""GameCloud Ranking API: versión para Kubernetes, instrumentada para observabilidad.

Endpoints:
  GET  /ranking[?juego=doom]  -> top 10 por juego
  POST /scores                -> {"jugador": "ana", "juego": "doom", "puntaje": 9800}
  GET  /healthz               -> health check para las probes de Kubernetes
  GET  /metrics               -> métricas en formato Prometheus

Inyección de fallas (variables de entorno, para los escenarios del TP):
  ERROR_RATE         proporción de pedidos que devuelven 500 (0 a 1). Default: 0
  LATENCIA_MS        demora agregada a cada pedido, en milisegundos. Default: 0
  FALLAR_AL_INICIAR  si vale "true", el proceso termina al arrancar (CrashLoopBackOff)

Los puntajes se guardan en memoria: cada réplica tiene su propio ranking.
Para esta práctica alcanza; en producción irían a una base de datos.
"""
import json
import logging
import os
import random
import sys
import threading
import time
from datetime import datetime, timezone

from flask import Flask, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

JUEGOS = ["doom", "pacman"]
TOP = 10
ERROR_RATE = float(os.environ.get("ERROR_RATE", "0"))
LATENCIA_MS = int(os.environ.get("LATENCIA_MS", "0"))
POD = os.environ.get("HOSTNAME", "local")

# ---------------------------------------------------------------- logs en JSON
class JsonFormatter(logging.Formatter):
    def format(self, record):
        datos = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "msg": record.getMessage(),
            "pod": POD,
        }
        datos.update(getattr(record, "extra_campos", {}))
        return json.dumps(datos, ensure_ascii=False)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
log = logging.getLogger("gamecloud")
log.addHandler(handler)
log.setLevel(logging.INFO)
log.propagate = False
logging.getLogger("werkzeug").setLevel(logging.WARNING)


def registrar(nivel, mensaje, **campos):
    log.log(nivel, mensaje, extra={"extra_campos": campos})


# ---------------------------------------------------------------- métricas
PEDIDOS = Counter(
    "http_requests_total",
    "Pedidos HTTP atendidos",
    ["method", "ruta", "status"],
)
LATENCIA = Histogram(
    "http_request_duration_seconds",
    "Duración de los pedidos HTTP",
    ["method", "ruta"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
NO_MEDIR = {"/metrics", "/healthz"}

# ---------------------------------------------------------------- app
if os.environ.get("FALLAR_AL_INICIAR", "false").lower() == "true":
    registrar(logging.CRITICAL, "FALLAR_AL_INICIAR=true: el proceso termina al iniciar")
    sys.exit(1)

app = Flask(__name__)
ranking = {juego: {} for juego in JUEGOS}  # {juego: {jugador: mejor_puntaje}}
lock = threading.Lock()


@app.before_request
def antes():
    g.inicio = time.perf_counter()
    if request.path in NO_MEDIR:
        return None
    if LATENCIA_MS:
        time.sleep(LATENCIA_MS / 1000)
    if ERROR_RATE and random.random() < ERROR_RATE:
        return jsonify(error="error interno simulado"), 500
    return None


@app.after_request
def despues(resp):
    if request.path in NO_MEDIR:
        return resp
    duracion = time.perf_counter() - g.inicio
    # ruta = la plantilla de la ruta (/scores), no la URL completa: evita
    # crear una serie distinta por cada query string (cardinalidad)
    ruta = request.url_rule.rule if request.url_rule else "desconocida"
    PEDIDOS.labels(request.method, ruta, str(resp.status_code)).inc()
    LATENCIA.labels(request.method, ruta).observe(duracion)

    nivel = logging.ERROR if resp.status_code >= 500 else (
        logging.WARNING if resp.status_code >= 400 else logging.INFO)
    registrar(nivel, "pedido atendido", method=request.method, path=request.path,
              status=resp.status_code, duracion_ms=round(duracion * 1000, 1))
    return resp


@app.get("/ranking")
def get_ranking():
    juego = request.args.get("juego")
    if juego and juego not in JUEGOS:
        return jsonify(error=f"juego invalido, usar: {JUEGOS}"), 400
    with lock:
        resultado = {
            j: [{"jugador": k, "puntaje": v}
                for k, v in sorted(ranking[j].items(), key=lambda x: x[1], reverse=True)[:TOP]]
            for j in ([juego] if juego else JUEGOS)
        }
    return jsonify(resultado)


@app.post("/scores")
def post_score():
    datos = request.get_json(silent=True) or {}
    try:
        jugador = str(datos["jugador"]).strip().lower()
        juego = str(datos["juego"]).strip().lower()
        puntaje = int(datos["puntaje"])
    except (KeyError, ValueError, TypeError):
        return jsonify(error="se esperan los campos jugador, juego y puntaje (entero)"), 400
    if not jugador or juego not in JUEGOS or puntaje < 0:
        return jsonify(error=f"datos invalidos (juegos validos: {JUEGOS})"), 400

    with lock:
        anterior = ranking[juego].get(jugador)
        nuevo_record = anterior is None or puntaje > anterior
        if nuevo_record:
            ranking[juego][jugador] = puntaje
    return jsonify(jugador=jugador, juego=juego, puntaje=puntaje, nuevo_record=nuevo_record), 201


@app.get("/healthz")
def healthz():
    return jsonify(estado="ok")


@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


registrar(logging.INFO, "API iniciada", error_rate=ERROR_RATE, latencia_ms=LATENCIA_MS)
