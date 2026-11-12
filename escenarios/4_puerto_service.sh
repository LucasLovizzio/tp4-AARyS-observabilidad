#!/usr/bin/env bash
# Escenario 4: el Service manda el tráfico a un puerto donde nadie escucha.
# Simula un error de configuración (no pasa por Helm, como un cambio manual).
kubectl -n gamecloud patch service gamecloud-ranking --type json \
  -p '[{"op":"replace","path":"/spec/ports/0/targetPort","value":9999}]'
