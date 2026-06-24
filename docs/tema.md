# 📌 PoC 1 — Detección de Personas Dentro de una Zona Definida

> Proyecto de Machine Learning y Visión por Computadora orientado a la detección de objetos, personas y acciones, con foco en el control de acceso y monitoreo de zonas restringidas.

---

## 🔍 Contexto del problema

Muchas organizaciones necesitan monitorear áreas específicas mediante cámaras de seguridad para **controlar accesos, ocupación o permanencia** de personas. Actualmente este monitoreo suele realizarse **manualmente** por operadores que observan las cámaras, lo que lo hace costoso, propenso a errores y no escalable.

### Ejemplos de escenarios reales

| Escenario | Descripción |
|---|---|
| 🏭 Plantas industriales | Áreas restringidas con acceso limitado a personal autorizado |
| ✈️ Aeropuertos | Zonas de seguridad y sectores de embarque |
| 📦 Logística | Áreas de carga y descarga |
| 🚨 Emergencias | Puntos de evacuación y control de flujo |
| 🛒 Comercios | Espacios donde se requiere medir la ocupación |
| 👷 Industria | Verificación de uso de EPP (cascos, chalecos, guantes) |

---

## 🎯 Problema a solucionar

Desarrollar una solución basada en **Machine Learning y Visión por Computadora** capaz de:

- 🔎 Detectar personas en imágenes o video
- 📐 Determinar si se encuentran **dentro o fuera** de una zona predefinida (ROI)
- 📊 Generar **métricas y eventos** asociados a la ocupación de dicha zona

La solución debe responder preguntas como:

| Pregunta | Tipo de dato |
|---|---|
| ¿Cuántas personas hay dentro del área? | Conteo en tiempo real |
| ¿Cuántas están fuera? | Conteo en tiempo real |
| ¿Quién ingresó? | ID de track + timestamp |
| ¿Quién salió? | ID de track + timestamp |
| ¿Se superó la capacidad máxima permitida? | Alerta de evento |

---

## 🎯 Objetivo de la PoC

> Validar la **factibilidad** de utilizar técnicas de detección de objetos y análisis espacial para automatizar el monitoreo de zonas específicas, reduciendo la dependencia del factor humano.

---

## 📋 Requisitos funcionales

### 🟢 Nivel Mínimo

#### 1. Detección de personas
Identificar todas las personas presentes en la escena.

```
Persona 1 → Detectada ✓
Persona 2 → Detectada ✓
Persona 3 → Detectada ✓
```

#### 2. Obtención de coordenadas
Registrar la ubicación de cada persona mediante **Bounding Box**.

```
x      = 120 px
y      = 180 px
ancho  =  80 px
alto   = 190 px
```

#### 3. Clasificación espacial
Determinar para cada persona si está:
- ✅ **Dentro** de la zona definida
- ❌ **Fuera** de la zona definida

#### 4. Estadísticas básicas
Generar indicadores en tiempo real:

| Indicador | Descripción |
|---|---|
| `personas_detectadas` | Total de personas en escena |
| `personas_dentro` | Personas dentro de la ROI |
| `personas_fuera` | Personas fuera de la ROI |

---

### 🟡 Nivel Intermedio

**Tracking de individuos** con ID persistente entre frames.

```
ID 1 → Dentro  ✅
ID 2 → Fuera   ❌
ID 3 → Dentro  ✅
```

Esto permite conocer:

- 📥 **Ingresos:** quién entró y cuándo
- 📤 **Egresos:** quién salió y cuándo
- ⏱️ **Tiempo de permanencia** de cada individuo en la zona

---

### 🔴 Nivel Avanzado

**Eventos inteligentes** disparados automáticamente:

#### Evento 1 — Alerta por sobreocupación
```
IF personas_dentro > 10 THEN → ALERTA: Capacidad superada
```

#### Evento 2 — Alerta por permanencia excesiva
```
IF tiempo_en_zona(persona) > 5 min THEN → ALERTA: Permanencia prolongada
```

#### Evento 3 — Conteo automático de flujo
```
contador_ingresos  +=1  (al detectar una entrada)
contador_egresos   +=1  (al detectar una salida)
```

---

> [!NOTE]
> Esta PoC sirve como base para escalar hacia sistemas más complejos como verificación de vestimenta de seguridad (EPP), análisis de comportamiento o integración con sistemas de acceso físico (torniquetes, puertas automáticas).