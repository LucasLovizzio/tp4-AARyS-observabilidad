#!/usr/bin/env bash
# Escenario 1: la API devuelve 500 en el 20% de los pedidos
helm upgrade gamecloud-ranking "$(dirname "$0")/../charts/gamecloud-ranking" -n gamecloud \
  --reuse-values --set fallas.errorRate=0.2
