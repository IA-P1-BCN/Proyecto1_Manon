# Flujo de la aplicación — Fase 2

Cómo cambia el CLI en la Fase 2. Se añade un **menú de inicio** que separa dos perfiles, Conductor y Administrador, y se revisa qué hace `Ctrl+C` durante una carrera. Este documento cubre la **US-07** (tarifas configurables); la US-05 (histórico) añadirá una opción al menú de Administrador.

Todo lo que no aparece aquí sigue igual que en [`flujo-fase1.md`](flujo-fase1.md): iniciar, parar/arrancar, ver importe, finalizar, ayuda y opción no válida. Las razones de cada decisión están en [`decisions-fase2.md`](decisions-fase2.md).

---

## Diagrama

```mermaid
flowchart TD
    START(["Arranque: python -m taximetro.taximetro_app"]) --> CONF["Leer config/tarifas.json<br/>(si falta, se crea; si no es válido, tarifas por defecto)"]
    CONF --> BANNER["Mostrar banner:<br/>tarifas vigentes y opciones de cada perfil"]
    BANNER --> INICIO

    %% ============ MENÚ DE INICIO ============
    INICIO["MENÚ DE INICIO<br/>1) Conductor · 2) Administrador · 3) Salir"] --> R_INI{"¿Qué número?"}
    R_INI -->|1| COND
    R_INI -->|2| ADMIN
    R_INI -->|3| FIN(["Fin del programa"])
    R_INI -->|"otra cosa"| NV_INI["'Opción no válida…'"] --> INICIO
    INICIO -.->|"Ctrl+C · EOF"| FIN

    %% ============ CONDUCTOR ============
    COND{"¿Hay carrera activa?"}
    COND -->|No| SIN["SIN CARRERA<br/>1) Iniciar carrera · 2) Ayuda · 3) Volver"]
    SIN -->|"1 · 2 — igual que en la Fase 1"| COND
    SIN -->|3| INICIO
    SIN -.->|"Ctrl+C · EOF"| FIN

    COND -->|Sí| CON["CARRERA ACTIVA<br/>1) Parar/Arrancar · 2) Ver importe<br/>3) Finalizar carrera · 4) Ayuda"]
    CON -->|"1 · 2 · 3 · 4 — igual que en la Fase 1"| COND
    CON -.->|"Ctrl+C"| PREG["'Vas a salir del programa con la carrera nº N en curso.'<br/>1) Sí, finalizar la carrera y salir<br/>2) No, seguir con la carrera<br/>(el taxímetro sigue contando)"]
    PREG -->|2 · o un segundo Ctrl+C| COND
    PREG -->|"otra cosa"| NV_PREG["'Opción no válida…'"] --> PREG
    PREG -->|"1 · o EOF"| CIERRE["carrera.finalizar()<br/>'TOTAL A COBRAR: X,XX €'"]
    CON -.->|"EOF (Ctrl+D)"| CIERRE
    CIERRE --> FIN

    %% ============ ADMINISTRADOR ============
    ADMIN["ADMINISTRADOR<br/>1) Cambiar tarifas · 2) Volver"] --> R_ADM{"¿Qué número?"}
    R_ADM -->|2| INICIO
    R_ADM -->|"otra cosa"| NV_ADM["'Opción no válida…'"] --> ADMIN
    ADMIN -.->|"Ctrl+C · EOF"| FIN
    R_ADM -->|1| VIG["'Tarifas vigentes: parado … · en movimiento …'"]
    VIG --> P1[/"Nueva tarifa parado (€/s)"/]
    P1 --> P2[/"Nueva tarifa en movimiento (€/s)"/]
    P2 --> VAL{"¿Válidas?"}
    VAL -->|Sí| GUARDA["Taximetro.cambiar_tarifa()<br/>escribe config/tarifas.json<br/>'Tarifas guardadas: … Se aplican desde la próxima carrera.'"]
    GUARDA --> ADMIN
    VAL -->|No| ERR["Motivo + 'No se ha guardado nada.'"] --> ADMIN
    P1 -.->|"Ctrl+C"| CANC["'Cambio cancelado. No se ha guardado nada.'"]
    P2 -.->|"Ctrl+C"| CANC
    CANC --> ADMIN
```

Las flechas discontinuas son interrupciones del terminal. Todo lo demás es un número tecleado. Los números siguen siendo **locales a cada menú**.

---

## Decisiones visibles

### Se elige perfil al arrancar

El programa abre en el menú de inicio. **Conductor** es el taxímetro de la Fase 1. **Administrador** reúne las funciones de gestión: de momento, cambiar las tarifas.

`Salir` solo existe en el menú de inicio. Los menús de Conductor y Administrador tienen `Volver`, y el del conductor solo lo ofrece **sin carrera en curso**. Por eso nunca se puede llegar al Administrador con una carrera abierta, y al pasajero siempre se le cobra la tarifa que se anunció al iniciar su carrera.

En la Fase 2 el Administrador **no pide contraseña**. La contraseña llega con la US-08 (Fase 3), y este menú ya deja preparado dónde irá.

### Cambiar tarifas

- Se piden las dos tarifas en €/s. Se admite coma o punto decimal: `0,03` o `0.03`.
- Reglas: cada tarifa mayor que 0 y como máximo 1,00 €/s, con 2 decimales como mucho, y la de parado no mayor que la de en movimiento.
- Si algo no cumple, se explica el motivo, **no se guarda nada** y se vuelve al menú de Administrador.
- Si es válido, se escribe `config/tarifas.json` y la tarifa nueva se aplica **desde la próxima carrera**. La carrera ya cobrada conserva la suya.
- Si el fichero no se puede escribir, no se cambia nada: el fichero y el taxímetro nunca discrepan.

Mensajes posibles:

| Situación | Mensaje |
|---|---|
| No es un número | `«abc» no es un número. Escribe, por ejemplo, 0,03. No se ha guardado nada.` |
| 0, negativa o más de 1 €/s | `Cada tarifa debe ser mayor que 0 y como máximo 1,00 €/s. No se ha guardado nada.` |
| Más de 2 decimales | `Cada tarifa admite como máximo 2 decimales. No se ha guardado nada.` |
| Parado mayor que en movimiento | `La tarifa parado no puede ser mayor que la de en movimiento. No se ha guardado nada.` |
| Fichero no escribible | `No se pudo escribir el fichero de tarifas. No se ha guardado nada.` |
| Ctrl+C mientras se teclea | `Cambio cancelado. No se ha guardado nada.` |

### El fichero de tarifas

`config/tarifas.json`, en €/s:

```json
{
  "parado": 0.02,
  "en_movimiento": 0.05
}
```

Un técnico puede editarlo a mano con el programa cerrado. Se lee al arrancar. Si falta, se crea con las tarifas por defecto. Si no es válido, el programa arranca igualmente con las tarifas por defecto y **no toca el fichero**, para que el técnico pueda ver y corregir su error. El repositorio incluye `config/tarifas.example.json` como referencia del formato; el `tarifas.json` real no se versiona.

### Ctrl+C durante una carrera pide confirmación

En la Fase 1, `Ctrl+C` a mitad de carrera se ignoraba con un aviso. En la Fase 2 pregunta:

```
Vas a salir del programa con la carrera nº 1 en curso.
  1) Sí, finalizar la carrera y salir
  2) No, seguir con la carrera
```

- **Mientras se pregunta, el taxímetro sigue contando** tiempo y dinero.
- **No** vuelve a la carrera como si nada hubiera pasado.
- **Sí** finaliza la carrera, muestra `TOTAL A COBRAR` y cierra el programa.
- Un **segundo Ctrl+C** cuenta como *No*: un doble toque por nervios no termina una carrera.
- **EOF** (`Ctrl+D`) cuenta como *Sí*, igual que EOF durante una carrera en la Fase 1.

Fuera de una carrera (menú de inicio, Administrador, conductor sin carrera), `Ctrl+C` y `Ctrl+D` cierran el programa directamente: no hay importe que perder.
