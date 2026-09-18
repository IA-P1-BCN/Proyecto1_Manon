# 🚕 TaxiTech Solutions — Sistema de Taxímetro Digital

---

> **Proyecto:** `TTX-247` — Modernización del sistema de facturación en flota
>
> **Cliente:** TaxiTech Solutions S.L. *(empresa de gestión de flotas de taxi, Madrid)*
>
> **Equipo asignado:** Backend Squad — Nuevas incorporaciones
>
> **Deadline:** Una semana a partir de la fecha de inicio del proyecto.

---

## 📩 Contexto del Encargo

El equipo de operaciones de **TaxiTech Solutions** lleva desde 2018 usando taxímetros físicos de la marca Hale modelo T200. El fabricante dejó de dar soporte en 2023 y los dispositivos están empezando a fallar en flota.

La dirección ha tomado la decisión de **migrar a un sistema 100% software** antes de Q3 2025. El CTO ha abierto este proyecto piloto para validar el concepto con un **prototipo funcional** antes de comprometer presupuesto con un proveedor externo.

Tu equipo ha sido asignado para desarrollar el prototipo.

---

## 🗣️ Briefing del Cliente

> *"Necesitamos algo que los taxistas puedan arrancar al inicio del turno y que calcule lo que le cuesta al pasajero en tiempo real. Cuando el taxi está parado en un semáforo, el contador sigue corriendo pero más despacio. En marcha, corre más rápido. Al llegar al destino, el taxista pulsa un botón, sale el total, y listo. Nos gustaría también poder ver un histórico de carreras del día. Si puede tener contraseña para que no lo toquen los pasajeros, mejor. Y si en el futuro se puede ver desde el móvil o una tablet en el taxi, perfecto."*
>
> — Director de Operaciones, TaxiTech Solutions

### Tarifas vigentes

**Zona EMT Madrid — junio 2025**

| Estado del taxi | Tarifa |
|---|---:|
| 🚕 Parado o velocidad < 20 km/h | `0.02 €/segundo` |
| 🚕 En movimiento | `0.05 €/segundo` |

---

## 📋 Historias de Usuario

| ID | Historia | Prioridad |
|---|---|---|
| **US-01** | Como taxista, quiero iniciar una carrera con un solo comando para empezar a cobrar desde el momento de arranque | **Must** |
| **US-02** | Como taxista, quiero cambiar el estado entre "parado" y "en movimiento" para que la tarifa se ajuste | **Must** |
| **US-03** | Como taxista, quiero finalizar la carrera y ver el total en euros para cobrar al pasajero | **Must** |
| **US-04** | Como taxista, quiero poder iniciar otra carrera sin cerrar el programa para no perder tiempo entre servicios | **Must** |
| **US-05** | Como responsable de flota, quiero ver el histórico de carreras del día para cuadrar caja | **Should** |
| **US-06** | Como técnico, quiero que el sistema genere logs de operación para diagnosticar errores en producción | **Should** |
| **US-07** | Como técnico, quiero poder cambiar las tarifas en un fichero de configuración sin redeployar | **Should** |
| **US-08** | Como responsable de flota, quiero que el sistema requiera contraseña para protegerlo de manipulaciones | **Could** |
| **US-09** | Como taxista, quiero una interfaz visual con botones grandes para usarlo fácilmente con el móvil o tablet | **Could** |

---

## 📊 Fases de Entrega

### 🟢 Fase 1 — MVP Funcional (US-01 a US-04)

CLI operativo que cubra el flujo completo de una carrera. Arranca desde terminal, presenta instrucciones de uso, permite gestionar el estado del vehículo por teclado. La tarifa se acumula de forma continua según el estado activo y el tiempo transcurrido. Al finalizar, importe total en euros con dos decimales. El proceso no se cierra entre carreras.

**Requisitos funcionales:**
- [ ] Al arrancar, el sistema explica al conductor cómo usarlo sin documentación externa.
- [ ] El conductor puede indicar en cada momento si el vehículo está parado o en movimiento.
- [ ] El importe se acumula de forma continua según estado activo y tiempo transcurrido, aplicando la tarifa correspondiente en cada tramo.
- [ ] Al cerrar la carrera, se muestra el importe total a cobrar.
- [ ] Se pueden encadenar carreras de forma inmediata, sin interrupciones.

### 🟡 Fase 2 — Observabilidad y Persistencia (US-05, US-06, US-07)

**Requisitos funcionales:**
- [ ] Registro de todo lo relevante: arranque, cambios de estado, cierre de carrera, errores.
- [ ] Registro accesible para el equipo técnico sin intervenir en el proceso en ejecución.
- [ ] Al finalizar cada carrera, los datos (fecha, duración, importe) quedan guardados de forma permanente.
- [ ] Datos disponibles en sesiones posteriores sin acción manual.
- [ ] Tarifas actualizables sin modificar código ni redeployar.
- [ ] Lógica de cálculo de tarifas cubierta por tests automatizados.

### 🟠 Fase 3 — Arquitectura y Experiencia de Usuario (US-08, US-09)

Refactorización estructural bajo un modelo OOP con responsabilidades claramente delimitadas, más interfaz gráfica táctil para tablet.

**Requisitos funcionales:**
- [ ] Cada componente tiene una responsabilidad clara y puede modificarse/sustituirse sin afectar al resto.
- [ ] Acceso protegido por contraseña.
- [ ] Credenciales almacenadas de forma segura; ningún valor sensible en texto plano.
- [ ] Interfaz gráfica funcional en tablet montada en el vehículo.
- [ ] Estado del taxi visible de un vistazo; importe actualizado en tiempo real.
- [ ] Interacción táctil cómoda; la interfaz no se bloquea durante el uso.

### 🔴 Fase 4 — Versión de Producción

Historial migra a base de datos relacional; lógica de negocio expuesta vía API REST; despliegue con un único comando.

**Requisitos funcionales:**
- [ ] Historial en base de datos con integridad y consultas estructuradas.
- [ ] API que permite iniciar carreras, cambiar estado, finalizarlas, consultar historial.
- [ ] API consumible por cualquier cliente web o móvil futuro.
- [ ] Panel web accesible desde navegador; responsable de flota consulta historial sin instalar nada.
- [ ] Despliegue con un único comando; sin configuración manual del entorno.
- [ ] Datos sobreviven a reinicios del sistema.

---

## 🛠️ Restricciones Técnicas

- Lenguaje: **Python**. Librerías/frameworks a elección del equipo, justificando decisiones en la documentación.
- Control de versiones: **Git y GitHub** desde el inicio.
- Gestión de tareas visible en tablero **GitHub Projects**, una columna por fase.

## 📦 Entregables por Fase

1. Repositorio de GitHub con el código fuente.
2. Demo en directo.
3. Enlace al tablero Kanban actualizado.

## 📚 Recursos

- [`time`](https://docs.python.org/3/library/time.html) — Python stdlib
- [`logging`](https://docs.python.org/3/library/logging.html) — Python stdlib
- [`unittest`](https://docs.python.org/3/library/unittest.html) — Python stdlib
- [`tkinter`](https://docs.python.org/3/library/tkinter.html) — GUI básica
- [Real Python — OOP en Python](https://realpython.com/python3-object-oriented-programming/)
- [Real Python — Testing](https://realpython.com/pytest-python-testing/)
- [Real Python — Logging](https://realpython.com/python-logging/)
- [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/)