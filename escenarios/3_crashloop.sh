#!/usr/bin/env bash
# Escenario 3: los pods nuevos de la API terminan al iniciar
helm upgrade gamecloud-ranking "$(dirname "$0")/../charts/gamecloud-ranking" -n gamecloud \
  --reuse-values --set fallas.fallarAlIniciar=true
