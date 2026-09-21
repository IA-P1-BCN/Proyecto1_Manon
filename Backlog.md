# Backlog — Taxímetro (Backend Python, POO)

Tablero: [IAS_P1_Taximetro_Manon](https://github.com/orgs/IA-P1-BCN/projects/2) · issues en [`IA-P1-BCN/Proyecto1_Manon`](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues).

- **Columnas** (campo `Status`): `User Stories` · `Fase 1` · `Fase 2` · `Fase 3` · `Fase 4` — una por fase, como pide el cliente.
- **Progreso** (campo `Progreso`): `To Do` · `En curso` · `En review` · `Done` — el avance del día a día no se marca moviendo tarjetas entre fases.
- **Prioridad**: `must`, `should`, `could`
- **Tipo**: `epic`, `feature`, `tech-task`, `test`, `docs`

Cada tarea técnica es un issue individual, enlazado aquí por su número. Las historias de usuario son issues épicas.

---

## EPIC 0 — Setup del proyecto (infraestructura) — [#11](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/11)
*Prioridad: Must — no viene de una US pero es prerequisito*

- [x] **T0.1** Crear estructura de paquete Python (`taximetro/`, `tests/`) ✅ — [#12](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/12)
  - Labels: `tech-task`, `must`
- [x] **T0.2** Configurar entorno virtual, `requirements.txt` / `pyproject.toml` ✅ — [#13](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/13)
  - Labels: `tech-task`, `must`
  - `.venv/` (Python 3.14.7) + `requirements-dev.txt` (pytest, pytest-cov) + `pyproject.toml` + `.gitignore`
- [x] **T0.3** Configurar framework de tests (`pytest`) ✅ — [#14](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/14)
  - Labels: `tech-task`, `must`
- [x] **T0.4** README inicial con instrucciones de instalación y uso — [#15](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/15) ✅
  - Labels: `docs`, `should`

---

## US-01 — Iniciar carrera con un solo comando (Must) — [#2](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/2)
**Como** taxista, **quiero** iniciar una carrera con un solo comando **para** empezar a cobrar desde el arranque.

**Criterios de aceptación**
- Dado que el taxímetro está inactivo, cuando ejecuto el comando de inicio, entonces se crea una nueva carrera con hora de inicio y el cobro comienza inmediatamente.
- El sistema debe impedir iniciar una carrera si ya hay una activa.

**Diseño sugerido**: clase `Carrera` (atributos: `id`, `hora_inicio`, `estado`, `distancia`, `importe`); clase `Taximetro` con método `iniciar_carrera()`.

Tareas:
- [x] **T1.1** Diseñar e implementar clase `Carrera` (estado inicial, atributos base) — `tech-task`, `must` — [#16](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/16) ✅
- [x] **T1.2** Implementar `Taximetro.iniciar_carrera()` con validación de "no hay carrera activa" — `tech-task`, `must` — [#17](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/17) ✅
- [x] **T1.3** Comando CLI `iniciar` (entrypoint) — `feature`, `must` — [#18](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/18) ✅
- [x] **T1.4** Tests unitarios: inicio correcto, inicio duplicado bloqueado — `test`, `must` — [#19](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/19) ✅

---

## US-02 — Cambiar estado parado / en movimiento (Must) — [#3](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/3)
**Como** taxista, **quiero** cambiar el estado entre "parado" y "en movimiento" **para** que la tarifa se ajuste.

**Criterios de aceptación**
- El sistema aplica una tarifa distinta (`0,02 €/s` parado vs `0,05 €/s` en movimiento) según el estado actual.
  - *Corregido: el texto original decía «€/min parado vs €/km en movimiento», que contradice las tarifas del briefing. El taxímetro cobra por segundo en ambos estados y nunca por distancia — ver `docs/project-brief.md`.*
- Cambiar de estado no interrumpe el cálculo acumulado del importe.

**Diseño sugerido**: `Carrera.cambiar_estado(nuevo_estado)`; clase `Tarifa` con métodos `calcular_parado()` / `calcular_movimiento()`.

> **Decisión tomada**: un único `Tarifa.calcular_importe(estado, segundos)` en lugar de un método por estado, para no duplicar el if/else de estado→tarifa en cada punto de llamada. La `Tarifa` la crea `Taximetro` y se la inyecta a cada `Carrera`. Ver `docs/decisions-fase1-scaffold.md`.

Tareas:
- [x] **T2.1** Implementar `Carrera.cambiar_estado()` con máquina de estados simple (parado/movimiento) — `tech-task`, `must` — [#20](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/20) ✅
- [x] **T2.2** Implementar clase `Tarifa` con lógica diferenciada de cálculo — `tech-task`, `must` — [#21](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/21) ✅
- [x] **T2.3** Integrar acumulación de importe en tiempo real al cambiar de estado — `tech-task`, `must` — [#22](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/22) ✅
- [x] **T2.4** Comando CLI para alternar estado — `feature`, `must` — [#23](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/23) ✅
- [x] **T2.5** Tests: cálculo correcto en cada estado y en transiciones — `test`, `must` — [#24](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/24) ✅

---

## US-03 — Finalizar carrera y ver total en euros (Must) — [#4](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/4)
**Como** taxista, **quiero** finalizar la carrera y ver el total en euros **para** cobrar al pasajero.

**Criterios de aceptación**
- Al finalizar, se muestra el importe total formateado en euros (2 decimales, símbolo €).
- La carrera finalizada queda marcada como cerrada y no admite más cambios de estado.

Tareas:
- [x] **T3.1** Implementar `Carrera.finalizar()` (cierre, cálculo final, hora de fin) — `tech-task`, `must` — [#25](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/25) ✅
- [x] **T3.2** Formateo de importe en euros (helper/util) — `tech-task`, `must` — [#26](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/26) ✅
- [x] **T3.3** Comando CLI `finalizar` que muestra el total — `feature`, `must` — [#27](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/27) ✅
- [x] **T3.4** Tests: importe final correcto, bloqueo de cambios tras finalizar — `test`, `must` — [#28](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/28) ✅

---

## US-04 — Iniciar otra carrera sin cerrar el programa (Must) — [#5](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/5)
**Como** taxista, **quiero** poder iniciar otra carrera sin cerrar el programa **para** no perder tiempo entre servicios.

**Criterios de aceptación**
- Tras finalizar una carrera, el programa vuelve a un estado "listo" y permite iniciar una nueva sin reiniciar el proceso.

**Diseño sugerido**: clase `TaximetroApp` (orquestador con bucle principal / menú de comandos) que gestiona el ciclo de vida de `Carrera`.

Tareas:
- [x] **T4.1** Implementar bucle principal / menú de comandos en `TaximetroApp` — `tech-task`, `must` — [#29](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/29) ✅
- [x] **T4.2** Reset de estado tras finalizar carrera (permitir nueva instancia) — `tech-task`, `must` — [#30](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/30) ✅
- [x] **T4.3** Tests de integración: ciclo completo iniciar→finalizar→iniciar — `test`, `must` — [#31](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/31) ✅

---

## US-05 — Histórico de carreras del día (Should) — [#6](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/6)
**Como** responsable de flota, **quiero** ver el histórico de carreras del día **para** cuadrar caja.

**Criterios de aceptación**
- El sistema guarda cada carrera finalizada (hora inicio/fin, importe, distancia).
- Existe un comando que muestra el listado del día y el total acumulado.

**Diseño sugerido**: clase `Historial` con persistencia en CSV/JSON; método `resumen_del_dia()`.

Tareas:
- [ ] **T5.1** Implementar clase `Historial` (registro de carreras) — `tech-task`, `should` — [#32](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/32)
- [ ] **T5.2** Persistencia en fichero (CSV o JSON) — `tech-task`, `should` — [#33](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/33)
- [ ] **T5.3** Comando `historial` con resumen y total de caja del día (opción «Ver histórico» del Administrador) — `feature`, `should` — [#34](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/34)
- [ ] **T5.4** Tests de persistencia y cálculo de totales — `test`, `should` — [#35](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/35)

---

## US-06 — Logs de operación (Should) — [#7](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/7)
**Como** técnico, **quiero** que el sistema genere logs de operación **para** diagnosticar errores en producción.

**Criterios de aceptación**
- Se registran eventos clave: inicio/fin de carrera, cambios de estado, errores.
- Los logs incluyen timestamp y nivel (INFO/WARNING/ERROR).

Tareas:
- [ ] **T6.1** Configurar módulo `logging` (formato, niveles, salida a fichero) — `tech-task`, `should` — [#36](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/36)
- [ ] **T6.2** Instrumentar eventos clave en `Carrera` / `Taximetro` — `tech-task`, `should` — [#37](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/37)
- [ ] **T6.3** Rotación de logs (`RotatingFileHandler`) — `tech-task`, `should` — [#38](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/38)
- [ ] **T6.4** Tests de logging (verificar que se generan entradas) — `test`, `should` — [#39](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/39)

---

## US-07 — Tarifas configurables sin redeploy (Should) — [#8](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/8)
**Como** técnico, **quiero** poder cambiar las tarifas en un fichero de configuración **para** no redeployar.

**Criterios de aceptación**
- Las tarifas (€/s parado, €/s en movimiento) se leen de un fichero externo (JSON/YAML) al arrancar.
- Si el fichero es inválido o falta, se usan valores por defecto sin que el programa falle.

**Diseño sugerido**: clase `ConfigTarifas` que carga y valida el fichero; inyectada en `Tarifa`.

Tareas:
- [ ] **T7.1** Definir esquema del fichero de configuración (`config/tarifas.json`) — `tech-task`, `should` — [#40](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/40)
- [ ] **T7.2** Implementar `ConfigTarifas` (carga, validación, defaults) — `tech-task`, `should` — [#41](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/41)
- [ ] **T7.3** Integrar `ConfigTarifas` en `Tarifa` — `tech-task`, `should` — [#42](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/42)
- [ ] **T7.4** Tests: fichero válido, fichero corrupto/ausente → defaults — `test`, `should` — [#43](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/43)
- [ ] **T7.5** Menú de roles al arrancar (`Conductor` · `Administrador` · `Salir`) — `feature`, `should` — [#84](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/84)
- [ ] **T7.6** Opción de Administrador: cambiar tarifas y guardar el fichero — `feature`, `should` — [#85](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/85)

*T7.5 y T7.6 no vienen del cliente: salen de la separación Conductor / Administrador decidida para la Fase 2 (ver `docs/decisions-fase2.md`). El menú de roles llega con US-07 porque es la primera historia que necesita el modo Administrador.*

---

## US-08 — Protección por contraseña (Could) — [#9](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/9)
**Como** responsable de flota, **quiero** que el sistema requiera contraseña **para** protegerlo de manipulaciones.

**Criterios de aceptación**
- El programa solicita contraseña antes de permitir operaciones sensibles (p.ej. iniciar el turno).
- La contraseña no se almacena en texto plano.

Tareas:
- [ ] **T8.1** Implementar clase `Auth` con verificación de contraseña — `tech-task`, `could` — [#44](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/44)
- [ ] **T8.2** Almacenamiento con hash (p.ej. `hashlib`/`bcrypt`) — `tech-task`, `could` — [#45](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/45)
- [ ] **T8.3** Integrar `Auth` en el arranque de `TaximetroApp` — `tech-task`, `could` — [#46](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/46)
- [ ] **T8.4** Tests de autenticación (correcta/incorrecta) — `test`, `could` — [#47](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/47)

---

## US-09 — Interfaz visual con botones grandes (Could) — [#10](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/10)
**Como** taxista, **quiero** una interfaz visual con botones grandes **para** usarlo fácilmente en móvil o tablet.

**Criterios de aceptación**
- Existe una UI gráfica (no solo CLI) con botones grandes para iniciar/cambiar estado/finalizar.
- La UI se apoya en la lógica de backend ya existente sin duplicarla.

*Nota: esta historia es "Could" y depende de que el backend (US-01 a US-04) esté estable primero.*

Tareas:
- [ ] **T9.1** Spike técnico: elegir framework de UI (Kivy / PyQt / Flask+webview) — `tech-task`, `could` — [#48](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/48)
- [ ] **T9.2** Diseñar pantalla principal (botones grandes, tipografía táctil) — `tech-task`, `could` — [#49](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/49)
- [ ] **T9.3** Conectar UI a la capa de backend (`Taximetro`/`TaximetroApp`) — `tech-task`, `could` — [#50](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/50)
- [ ] **T9.4** Tests manuales/UX en dispositivo táctil — `test`, `could` — [#51](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/51)

---

## EPIC D — Decisiones de diseño del flujo CLI (Fase 1)
*Prioridad: Must — no deriva de una US, sino de decisiones tomadas al dibujar el flujo antes de implementar*

Referencia: **`docs/flujo-fase1.md`** (diagrama Mermaid + registro de decisiones). Issue épica: [#52](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/52).

Estas tareas no añaden funcionalidad nueva al producto, pero definen el comportamiento del bucle CLI. Sin ellas, dos requisitos funcionales de Fase 1 quedan a medias: *"el sistema explica al conductor cómo usarlo sin documentación externa"* y *"calcule lo que le cuesta al pasajero en tiempo real"*.

| Decisión | Efecto |
|---|---|
| Menús contextuales | El conductor solo ve las opciones válidas en cada momento |
| Menú numerado | Se teclea un número, no un comando; los números son locales a cada menú |
| Una sola opción de estado | El menú ofrece `Parar` o `Arrancar`, siempre lo contrario de lo actual |
| La carrera nace EN MOVIMIENTO | Se inicia cuando el taxi arranca: 0,05 €/s desde el primer segundo |
| `Salir` fuera del menú de carrera activa | `Finalizar carrera` termina la carrera, `Salir` termina el programa |
| Opción `Ver importe` | Total acumulado bajo demanda, solo lectura |
| Opción `Ayuda` | Reimprime el banner cuando se ha ido de pantalla |
| Ctrl+C gestionado | Una carrera solo termina de forma deliberada |
| Un único error posible | Lo que no es un número del menú se rechaza sin tocar la carrera |

Tareas:
- [x] **TD.1** Diagrama de flujo del CLI de Fase 1 — `docs`, `must` — [#53](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/53) ✅
- [x] **TD.2** Menús contextuales según estado de la carrera — `feature`, `must` — [#54](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/54) ✅
- [x] **TD.3** Comando CLI `importe` (total acumulado bajo demanda) — `feature`, `must` — [#55](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/55) ✅
- [x] **TD.4** Implementar `Carrera.importe_actual()` sin mutación — `tech-task`, `must` — [#56](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/56) ✅
- [x] **TD.5** Test: `importe_actual()` no altera el importe acumulado — `test`, `must` — [#57](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/57) ✅
- [x] **TD.6** Comando CLI `ayuda` (reimprimir banner) — `feature`, `must` — [#58](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/58) ✅
- [x] **TD.7** Gestión de Ctrl+C según el estado del bucle — `tech-task`, `must` — [#59](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/59) ✅
- [x] ~~**TD.8** Mensajes de error diferenciados en el CLI~~ — `feature`, `must` — [#60](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/60) — *superada por TD.10: cerrada como no planificada*
- [x] **TD.9** Tests del bucle CLI: menús, errores y Ctrl+C — `test`, `must` — [#61](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/61) ✅

**Orden sugerido:** TD.4 → TD.5 → TD.3 (el accesor de solo lectura y su test de regresión antes del comando que lo usa), luego TD.2 → TD.8 → TD.7 (los menús contextuales primero, porque los otros dos dependen de que el bucle sepa en qué modo está), TD.6 en cualquier momento, y TD.9 al final.

**Relación con tareas existentes:** TD.2 concreta cómo debe comportarse el menú de **T4.1**; TD.9 complementa **T4.3** cubriendo las ramas de error y Ctrl+C que el ciclo funcional no toca.

**Revisión posterior (cambio de CLI a menú numerado).** A petición del cliente, el CLI pasó de comandos escritos a un menú numerado, la opción de estado se convirtió en un único conmutador `Parar`/`Arrancar` y la carrera pasa a nacer `EN_MOVIMIENTO`. Efecto sobre las tareas ya cerradas de este épico:

- **TD.2**, **TD.3**, **TD.6**, **TD.7**, **TD.9** siguen vigentes; solo cambia la forma de la entrada (un número en vez de una palabra).
- **TD.8** (mensajes de error diferenciados) queda **superada**: con el menú numerado el caso "comando correcto en el modo equivocado" no puede darse, así que solo queda un mensaje de error. El razonamiento está en `docs/flujo-fase1.md`.
Tareas de la revisión:
- [x] **TD.10** Menú numerado en lugar de comandos escritos — `feature`, `must` — [#80](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/80) ✅
- [x] **TD.11** Opción única `Parar`/`Arrancar` en lugar de `parado` y `movimiento` — `feature`, `must` — [#81](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/81) ✅
- [x] **TD.12** La carrera nace `EN_MOVIMIENTO` — `tech-task`, `must` — [#82](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/82) ✅

---

## EPIC P — Decisiones de la sesión previa a la implementación — [#62](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/62)
*Prioridad: Must — no deriva de una US, sino de la sesión de diseño anterior a escribir la lógica de Fase 1*

Referencia: **`docs/decisions-fase1-scaffold.md`** (decisiones de código) y **`docs/decisions-proceso.md`** (decisiones de proceso).

El andamiaje daba por decididas cosas que no lo estaban — de dónde sale la `Tarifa`, qué pasa al leer una carrera cerrada, cómo se testea el bucle CLI — y arrastraba una contradicción de formato entre documentos. Estas tareas lo corrigen antes de que el código las fije.

| Decisión | Efecto |
|---|---|
| Dos relojes inyectables | Un salto del reloj de pared ya no puede restar importe |
| Lectura congelada tras `finalizar()` | El total de una carrera cerrada deja de crecer |
| `Tarifa` inyectada desde `Taximetro` | La Fase 2 (US-07) no tendrá que tocar `Carrera` |
| `entrada` / `salida` inyectables | El bucle CLI se puede testear (TD.9) |
| EOF gestionado | Ni traceback ni importe perdido con Ctrl+D o entrada canalizada |
| Formato `12,34 €` | Se resuelve la contradicción entre el andamiaje y el flujo |

Tareas:
- [x] **TP.1** Dos relojes inyectables: `monotonic` para acumular, calendario para las horas — `tech-task`, `must` — [#63](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/63) ✅
- [x] **TP.2** Lectura congelada en una carrera finalizada — `tech-task`, `must` — [#64](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/64) ✅
- [x] **TP.3** Inyección de `entrada`/`salida` en `TaximetroApp` — `tech-task`, `must` — [#65](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/65) ✅
- [x] **TP.4** Gestión de EOF (Ctrl+D) en el bucle CLI — `feature`, `must` — [#66](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/66) ✅
- [x] **TP.5** `formato_euros` en formato español (`12,34 €`) — `tech-task`, `must` — [#67](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/67) ✅
- [x] **TP.6** Campo `Progreso` en el tablero — `tech-task`, `must` — [#68](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/68) ✅ *(la segunda vista filtrada se descartó: `Progreso` ya basta)*
- [x] **TP.7** Unificar el brief del cliente en `docs/project-brief.md` — `docs`, `must` — [#69](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/69) ✅
- [x] **TP.8** Workflow de CI: `pytest` en cada push y PR — `tech-task`, `must` — [#70](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/70) ✅
- [x] **TP.9** Umbral de cobertura del 90 % en `pyproject.toml` — `test`, `must` — [#71](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/71) ✅
- [x] **TP.10** README mínimo en español — `docs`, `should` — [#72](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/72) ✅
- [x] **TP.11** Guion de la demo de Fase 1 — `docs`, `must` — [#73](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/73) ✅
- [x] **TP.12** `conftest` con relojes falsos y test de estructura — `test`, `must` — [#74](https://github.com/IA-P1-BCN/Proyecto1_Manon/issues/74) ✅

**Relación con tareas existentes:** TP.1 se implementa junto a **T1.1** (clase `Carrera`); TP.3 junto a **T4.1** (bucle principal); TP.4 junto a **TD.7** (gestión de Ctrl+C), que es la otra mitad de la misma rama del bucle; TP.5 concreta el formato que produce **T3.2**.

---

## Resumen de prioridades (para ordenar el Sprint 1)

| Prioridad | Historias |
|---|---|
| Must | US-01, US-02, US-03, US-04, EPIC D, EPIC P |
| Should | US-05, US-06, US-07 |
| Could | US-08, US-09 |

Sugerencia: Sprint 1 = Epic 0 + US-01 a US-04 + EPIC D + EPIC P (núcleo funcional del taxímetro). Sprint 2 = US-05 a US-07 (operación/producción). Sprint 3 = US-08, US-09 (extras).