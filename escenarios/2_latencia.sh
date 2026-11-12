#!/usr/bin/env bash
# Escenario 2: cada pedido tarda 2 segundos más
helm upgrade gamecloud-ranking "$(dirname "$0")/../charts/gamecloud-ranking" -n gamecloud \
  --reuse-values --set fallas.latenciaMs=2000
