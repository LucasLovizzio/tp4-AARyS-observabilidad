# Escenarios de falla

Cada script modifica la API en el namespace `gamecloud` (release `gamecloud-ranking`).
Después de activar un escenario, esperar 1 o 2 minutos para que los cambios se reflejen en las métricas.

| Script | Falla que provoca |
|---|---|
| `1_errores.sh` | La API devuelve error 500 en el 20% de los pedidos |
| `2_latencia.sh` | Cada pedido tarda 2 segundos más |
| `3_crashloop.sh` | Los pods nuevos de la API terminan al iniciar |
| `4_puerto_service.sh` | El Service envía el tráfico a un puerto donde no escucha nadie |
| `normal.sh` | Vuelve todo al estado normal |

Ejecutar los scripts desde la raíz del repositorio, por ejemplo: `bash escenarios/1_errores.sh`.
