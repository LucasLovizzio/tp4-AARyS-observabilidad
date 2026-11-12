#!/usr/bin/env bash
# Vuelve la API al estado normal (también deshace el patch del escenario 4)
helm upgrade gamecloud-ranking "$(dirname "$0")/../charts/gamecloud-ranking" -n gamecloud \
  --set fallas.errorRate=0 --set fallas.latenciaMs=0 --set fallas.fallarAlIniciar=false

# Por las dudas, restaurar explícitamente el targetPort del Service
kubectl -n gamecloud patch service gamecloud-ranking --type json \
  -p '[{"op":"replace","path":"/spec/ports/0/targetPort","value":"http"}]'
