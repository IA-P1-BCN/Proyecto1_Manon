# Backlog — Taxímetro (Backend Python, POO)

Convención de etiquetas sugeridas para el tablero Kanban:
- **Prioridad**: `must`, `should`, `could`
- **Tipo**: `epic`, `feature`, `tech-task`, `test`, `docs`
- **Columnas del tablero**: `Backlog` → `To Do` → `In Progress` → `In Review` → `Done`

Cada tarjeta de "Tarea técnica" está pensada para ser un issue individual en GitHub, enlazado a la historia de usuario (Epic) mediante una checklist o `Related to #US-XX`.

---

## EPIC 0 — Setup del proyecto (infraestructura)
*Prioridad: Must — no viene de una US pero es prerequisito*

- [ ] **T0.1** Crear estructura de paquete Python (`taximetro/`, `tests/`, `config/`)
  - Labels: `tech-task`, `must`
- [ ] **T0.2** Configurar entorno virtual, `requirements.txt` / `pyproject.toml`
  - Labels: `tech-task`, `must`
- [ ] **T0.3** Configurar framework de tests (`pytest`)
  - Labels: `tech-task`, `must`
- [ ] **T0.4** README inicial con instrucciones de instalación y uso
  - Labels: `docs`, `should`

---

## US-01 — Iniciar carrera con un solo comando (Must)
**Como** taxista, **quiero** iniciar una carrera con un solo comando **para** empezar a cobrar desde el arranque.

**Criterios de aceptación**
- Dado que el taxímetro está inactivo, cuando ejecuto el comando de inicio, entonces se crea una nueva carrera con hora de inicio y el cobro comienza inmediatamente.
- El sistema debe impedir iniciar una carrera si ya hay una activa.

**Diseño sugerido**: clase `Carrera` (atributos: `id`, `hora_inicio`, `estado`, `distancia`, `importe`); clase `Taximetro` con método `iniciar_carrera()`.

Tareas:
- [ ] **T1.1** Diseñar e implementar clase `Carrera` (estado inicial, atributos base) — `tech-task`, `must`
- [ ] **T1.2** Implementar `Taximetro.iniciar_carrera()` con validación de "no hay carrera activa" — `tech-task`, `must`
- [ ] **T1.3** Comando CLI `iniciar` (entrypoint) — `feature`, `must`
- [ ] **T1.4** Tests unitarios: inicio correcto, inicio duplicado bloqueado — `test`, `must`

---

## US-02 — Cambiar estado parado / en movimiento (Must)
**Como** taxista, **quiero** cambiar el estado entre "parado" y "en movimiento" **para** que la tarifa se ajuste.

**Criterios de aceptación**
- El sistema aplica una tarifa distinta (€/min parado vs €/km en movimiento) según el estado actual.
- Cambiar de estado no interrumpe el cálculo acumulado del importe.

**Diseño sugerido**: `Carrera.cambiar_estado(nuevo_estado)`; clase `Tarifa` con métodos `calcular_parado()` / `calcular_movimiento()`.

Tareas:
- [ ] **T2.1** Implementar `Carrera.cambiar_estado()` con máquina de estados simple (parado/movimiento) — `tech-task`, `must`
- [ ] **T2.2** Implementar clase `Tarifa` con lógica diferenciada de cálculo — `tech-task`, `must`
- [ ] **T2.3** Integrar acumulación de importe en tiempo real al cambiar de estado — `tech-task`, `must`
- [ ] **T2.4** Comando CLI para alternar estado — `feature`, `must`
- [ ] **T2.5** Tests: cálculo correcto en cada estado y en transiciones — `test`, `must`

---

## US-03 — Finalizar carrera y ver total en euros (Must)
**Como** taxista, **quiero** finalizar la carrera y ver el total en euros **para** cobrar al pasajero.

**Criterios de aceptación**
- Al finalizar, se muestra el importe total formateado en euros (2 decimales, símbolo €).
- La carrera finalizada queda marcada como cerrada y no admite más cambios de estado.

Tareas:
- [ ] **T3.1** Implementar `Carrera.finalizar()` (cierre, cálculo final, hora de fin) — `tech-task`, `must`
- [ ] **T3.2** Formateo de importe en euros (helper/util) — `tech-task`, `must`
- [ ] **T3.3** Comando CLI `finalizar` que muestra el total — `feature`, `must`
- [ ] **T3.4** Tests: importe final correcto, bloqueo de cambios tras finalizar — `test`, `must`

---

## US-04 — Iniciar otra carrera sin cerrar el programa (Must)
**Como** taxista, **quiero** poder iniciar otra carrera sin cerrar el programa **para** no perder tiempo entre servicios.

**Criterios de aceptación**
- Tras finalizar una carrera, el programa vuelve a un estado "listo" y permite iniciar una nueva sin reiniciar el proceso.

**Diseño sugerido**: clase `TaximetroApp` (orquestador con bucle principal / menú de comandos) que gestiona el ciclo de vida de `Carrera`.

Tareas:
- [ ] **T4.1** Implementar bucle principal / menú de comandos en `TaximetroApp` — `tech-task`, `must`
- [ ] **T4.2** Reset de estado tras finalizar carrera (permitir nueva instancia) — `tech-task`, `must`
- [ ] **T4.3** Tests de integración: ciclo completo iniciar→finalizar→iniciar — `test`, `must`

---

## US-05 — Histórico de carreras del día (Should)
**Como** responsable de flota, **quiero** ver el histórico de carreras del día **para** cuadrar caja.

**Criterios de aceptación**
- El sistema guarda cada carrera finalizada (hora inicio/fin, importe, distancia).
- Existe un comando que muestra el listado del día y el total acumulado.

**Diseño sugerido**: clase `Historial` con persistencia en CSV/JSON; método `resumen_del_dia()`.

Tareas:
- [ ] **T5.1** Implementar clase `Historial` (registro de carreras) — `tech-task`, `should`
- [ ] **T5.2** Persistencia en fichero (CSV o JSON) — `tech-task`, `should`
- [ ] **T5.3** Comando `historial` con resumen y total de caja del día — `feature`, `should`
- [ ] **T5.4** Tests de persistencia y cálculo de totales — `test`, `should`

---

## US-06 — Logs de operación (Should)
**Como** técnico, **quiero** que el sistema genere logs de operación **para** diagnosticar errores en producción.

**Criterios de aceptación**
- Se registran eventos clave: inicio/fin de carrera, cambios de estado, errores.
- Los logs incluyen timestamp y nivel (INFO/WARNING/ERROR).

Tareas:
- [ ] **T6.1** Configurar módulo `logging` (formato, niveles, salida a fichero) — `tech-task`, `should`
- [ ] **T6.2** Instrumentar eventos clave en `Carrera` / `Taximetro` — `tech-task`, `should`
- [ ] **T6.3** Rotación de logs (`RotatingFileHandler`) — `tech-task`, `should`
- [ ] **T6.4** Tests de logging (verificar que se generan entradas) — `test`, `should`

---

## US-07 — Tarifas configurables sin redeploy (Should)
**Como** técnico, **quiero** poder cambiar las tarifas en un fichero de configuración **para** no redeployar.

**Criterios de aceptación**
- Las tarifas (€/km, €/min parado, bajada de bandera) se leen de un fichero externo (JSON/YAML) al arrancar.
- Si el fichero es inválido o falta, se usan valores por defecto sin que el programa falle.

**Diseño sugerido**: clase `ConfigTarifas` que carga y valida el fichero; inyectada en `Tarifa`.

Tareas:
- [ ] **T7.1** Definir esquema del fichero de configuración (`config/tarifas.json`) — `tech-task`, `should`
- [ ] **T7.2** Implementar `ConfigTarifas` (carga, validación, defaults) — `tech-task`, `should`
- [ ] **T7.3** Integrar `ConfigTarifas` en `Tarifa` — `tech-task`, `should`
- [ ] **T7.4** Tests: fichero válido, fichero corrupto/ausente → defaults — `test`, `should`

---

## US-08 — Protección por contraseña (Could)
**Como** responsable de flota, **quiero** que el sistema requiera contraseña **para** protegerlo de manipulaciones.

**Criterios de aceptación**
- El programa solicita contraseña antes de permitir operaciones sensibles (p.ej. iniciar el turno).
- La contraseña no se almacena en texto plano.

Tareas:
- [ ] **T8.1** Implementar clase `Auth` con verificación de contraseña — `tech-task`, `could`
- [ ] **T8.2** Almacenamiento con hash (p.ej. `hashlib`/`bcrypt`) — `tech-task`, `could`
- [ ] **T8.3** Integrar `Auth` en el arranque de `TaximetroApp` — `tech-task`, `could`
- [ ] **T8.4** Tests de autenticación (correcta/incorrecta) — `test`, `could`

---

## US-09 — Interfaz visual con botones grandes (Could)
**Como** taxista, **quiero** una interfaz visual con botones grandes **para** usarlo fácilmente en móvil o tablet.

**Criterios de aceptación**
- Existe una UI gráfica (no solo CLI) con botones grandes para iniciar/cambiar estado/finalizar.
- La UI se apoya en la lógica de backend ya existente sin duplicarla.

*Nota: esta historia es "Could" y depende de que el backend (US-01 a US-04) esté estable primero.*

Tareas:
- [ ] **T9.1** Spike técnico: elegir framework de UI (Kivy / PyQt / Flask+webview) — `tech-task`, `could`
- [ ] **T9.2** Diseñar pantalla principal (botones grandes, tipografía táctil) — `tech-task`, `could`
- [ ] **T9.3** Conectar UI a la capa de backend (`Taximetro`/`TaximetroApp`) — `tech-task`, `could`
- [ ] **T9.4** Tests manuales/UX en dispositivo táctil — `test`, `could`

---

## Resumen de prioridades (para ordenar el Sprint 1)

| Prioridad | Historias |
|---|---|
| Must | US-01, US-02, US-03, US-04 |
| Should | US-05, US-06, US-07 |
| Could | US-08, US-09 |

Sugerencia: Sprint 1 = Epic 0 + US-01 a US-04 (núcleo funcional del taxímetro). Sprint 2 = US-05 a US-07 (operación/producción). Sprint 3 = US-08, US-09 (extras).