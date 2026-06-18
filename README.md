<div align="center">

# 🎯 ML Person Detection

### Detección inteligente de personas en zonas definidas mediante Computer Vision

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![YOLOv11](https://img.shields.io/badge/YOLO-v11-00FFFF?style=for-the-badge&logo=ultralytics&logoColor=black)](https://ultralytics.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![Google Colab](https://img.shields.io/badge/Google%20Colab-Ready-F9AB00?style=for-the-badge&logo=googlecolab&logoColor=white)](https://colab.research.google.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**Grupo 7 · Majda · Ortega | Proyecto ML – GOTECHY**

</div>

---

## 📋 Tabla de Contenidos

- [¿De qué trata el proyecto?](#-de-qué-trata-el-proyecto)
- [Casos de uso](#-casos-de-uso)
- [Arquitectura del sistema](#-arquitectura-del-sistema)
- [Tecnologías utilizadas](#-tecnologías-utilizadas)
- [Requisitos previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Uso en Google Colab (recomendado)](#-uso-en-google-colab-recomendado)
- [Uso en local](#-uso-en-local)
- [Configuración del pipeline](#-configuración-del-pipeline)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Pipeline de procesamiento](#-pipeline-de-procesamiento)
- [Autores](#-autores)

---

## 🧠 ¿De qué trata el proyecto?

Este proyecto implementa un sistema de **detección y seguimiento de personas en tiempo real** utilizando técnicas de *Machine Learning* y *Visión por Computadora*. El caso principal consiste en monitorear una **escalera** y determinar cuántas personas suben, cuántas bajan y cuántas se encuentran dentro de una zona de interés (ROI) definida por el usuario.

El sistema es capaz de:

- 🔍 **Detectar personas** en un video utilizando YOLOv11 (clase 0 — persona)
- 🏷️ **Asignar un ID único persistente** a cada persona usando ByteTrack
- 📐 **Clasificar espacialmente** si cada persona está dentro o fuera del área definida (ROI poligonal)
- ↕️ **Determinar la dirección** del movimiento (subiendo / bajando)
- 📊 **Generar métricas y eventos** en tiempo real: ingresos, egresos, contadores globales
- 🎬 **Exportar el video anotado** con bounding boxes, IDs, eventos y estadísticas superpuestas

---

## 🌐 Casos de uso

Aunque el caso de referencia es una escalera, la arquitectura es genérica y puede adaptarse a múltiples escenarios del mundo real:

| Escenario | Descripción |
|---|---|
| 🏭 **Control de acceso industrial** | Detectar si personas ingresan a zonas restringidas de una planta sin autorización |
| 👷 **Verificación de EPP (Equipo de Protección Personal)** | Combinado con modelos adicionales, verificar si operarios usan casco, chaleco, guantes u otros elementos reglamentarios |
| 🛂 **Gestión de flujo en aeropuertos / edificios** | Contar personas que entran y salen de sectores de embarque, salas de espera o puntos de control |
| 🏪 **Análisis de ocupación en comercios** | Monitorear la cantidad de clientes en una sección para gestión de aforo |
| 🏥 **Hospitales y espacios con acceso restringido** | Detectar presencia no autorizada en quirófanos, laboratorios o zonas de aislamiento |
| 🎓 **Escuelas y universidades** | Conteo de ingreso/egreso en horarios de clases para seguridad |
| 🏗️ **Obras en construcción** | Supervisar que el personal use indumentaria y elementos de seguridad obligatorios |

> **Nota sobre vestimenta / EPP:** El pipeline está diseñado para ser extensible. Incorporando modelos de clasificación de atributos (ej. detección de cascos con `class_id` específico), el mismo sistema puede disparar alertas si una persona ingresa a la zona sin el equipo de trabajo correcto.

---

## 🏗️ Arquitectura del sistema

El proyecto sigue principios de **diseño orientado a interfaces** (ABCs), lo que lo hace modular, testeable y fácilmente extensible:

```
Video Input
    │
    ▼
┌─────────────────┐
│  ByteTrackTracker│  ← YOLOv11 + ByteTrack → Tracks con ID persistente
└────────┬────────┘
         │ list[Track]
         ▼
┌─────────────────┐
│ OpenCvRoiEngine │  ← cv2.pointPolygonTest → ¿está dentro del polígono?
└────────┬────────┘
         │ list[SpatialTrack]
         ▼
┌──────────────────────┐
│ InMemoryStateManager │  ← Detecta cambios de estado (dentro ↔ fuera)
└────────┬─────────────┘
         │ list[StateChange]
         ▼
┌────────────────────┐
│ DefaultEventEngine │  ← Clasifica: entered / exited / appeared_inside
└────────┬───────────┘
         │ list[Event]
         ▼
┌──────────────────┐
│ OpenCvVisualizer │  ← Dibuja ROI, bboxes, IDs, eventos y contadores
└────────┬─────────┘
         │
         ▼
   Video Output (MP4 anotado)
```

---

## 🛠️ Tecnologías utilizadas

| Librería | Versión | Función |
|---|---|---|
| `ultralytics` | ≥ 8.3 | Detección con YOLOv11 y tracking con ByteTrack |
| `opencv-python` | ≥ 4.10 | Procesamiento de video y análisis de ROI |
| `numpy` | ≥ 1.26 | Operaciones vectoriales y geometría |
| `torch` | ≥ 2.0 | Backend de inferencia (GPU/CPU) |
| `supervision` | ≥ 0.21 | Utilidades adicionales de visión por computadora |
| `ffmpeg` | sistema | Recodificación de video a H.264 compatible |

---

## ✅ Requisitos previos

- Python **3.10 o superior** (probado en 3.12)
- `git` instalado
- `ffmpeg` instalado en el sistema (para recodificación de video)
- GPU con CUDA (opcional pero recomendado para mayor velocidad de inferencia)
- Una cuenta de **Google** (si se usa Google Colab)

---

## 📥 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/FacundoMajda/ML-GOTECHY-G7-MAJDA-ORTEGA.git
cd ML-GOTECHY-G7-MAJDA-ORTEGA
```

### 2. Crear y activar el entorno virtual

#### En Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### En macOS / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

> 💡 Si en Windows aparece un error de permisos de ejecución de scripts, ejecutá primero:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3. Instalar las dependencias

```bash
pip install ultralytics supervision opencv-python numpy torch
```

> ⚡ Para usar GPU con CUDA, instalá PyTorch con soporte CUDA desde [pytorch.org](https://pytorch.org/get-started/locally/).

---

## ☁️ Uso en Google Colab (recomendado)

El notebook `ml_gotechy.ipynb` está diseñado para correr directamente en **Google Colab** aprovechando la GPU gratuita de T4.

### Pasos:

1. **Subir el notebook a Google Colab:**
   - Ir a [colab.research.google.com](https://colab.research.google.com)
   - `Archivo` → `Subir notebook` → seleccionar `ml_gotechy.ipynb`

2. **Activar la GPU:**
   - `Entorno de ejecución` → `Cambiar tipo de entorno de ejecución` → seleccionar **GPU T4**

3. **Subir el video al Drive o a `/content/sample_data/`:**
   ```python
   # El video debe estar en:
   VIDEO_PATH = "/content/sample_data/sample-p2.mp4"
   ```
   Podés montarlo desde Google Drive ejecutando la **Celda 3**:
   ```python
   from google.colab import drive
   drive.mount('/content/drive')
   ```

4. **Ejecutar las celdas en orden:**
   - **Celda 1:** Instala `ultralytics` y `supervision`
   - **Celda 2:** Importa todas las dependencias
   - **Celda 3:** Monta Google Drive
   - **Celda 4:** Verifica GPU disponible
   - **Celdas 5–13:** Define las clases del dominio y el pipeline
   - **Celda 14:** Configura la ROI y los contadores → instancia el pipeline
   - **Celda 15:** Reescala el video a 1080p con FFmpeg
   - **Celda 16:** Procesa el video frame a frame y exporta el resultado
   - **Celda 18:** Previsualiza la ROI sobre el primer frame
   - **Celda 19:** Lista los archivos MP4 generados

5. **Descargar el video procesado:**
   El video anotado se guarda como `output_h264.mp4` en `/content/`.

---

## 💻 Uso en local

Una vez instaladas las dependencias y activado el entorno virtual, podés ejecutar el notebook localmente con Jupyter:

```bash
pip install jupyter
jupyter notebook ml_gotechy.ipynb
```

> ⚠️ **Importante:** Al correr localmente, debés comentar o eliminar las líneas que usan `google.colab`:
> ```python
> # from google.colab import drive          ← comentar
> # from google.colab.patches import cv2_imshow  ← comentar, usar cv2.imshow() en su lugar
> # drive.mount('/content/drive')           ← comentar
> ```
> Y ajustar las rutas de video:
> ```python
> VIDEO_PATH = "ruta/local/a/tu/video.mp4"
> OUTPUT_PATH = "output.mp4"
> ```

---

## ⚙️ Configuración del pipeline

El parámetro más importante a configurar es el **polígono de la ROI** (Región de Interés), que define el área de la escalera (o cualquier zona) que queremos monitorear:

```python
# Celda 14 — Ajustá estos puntos según tu video
ROI_POLYGON = [
    [1824, 500],
    [1904, 436],
    [1122, 332],
    [984, 366]
]
```

### ¿Cómo obtener los puntos correctos?

Ejecutá la **Celda 18** para ver la ROI actual superpuesta sobre el primer frame del video. Ajustá los valores de `ROI_POLYGON` hasta que el polígono cubra exactamente la zona deseada.

También podés cambiar los parámetros del modelo:

```python
# Modelo YOLO a usar (yolo11n.pt = nano, más rápido; yolo11x.pt = extra large, más preciso)
tracker = ByteTrackTracker("yolo11n.pt", conf=0.3)
# conf: umbral de confianza mínima para considerar una detección (0.0 - 1.0)
```

---

## 📁 Estructura del proyecto

```
ML-GOTECHY-G7-MAJDA-ORTEGA/
│
├── ml_gotechy.ipynb        # Notebook principal con todo el pipeline
├── README.md               # Este archivo
├── tema.md                 # Descripción del problema (documento de la cátedra)
│
└── sample_data/            # Carpeta para videos de entrada
    └── sample-p2.mp4       # Video de ejemplo (no incluido en el repo — ver nota)
```

> 📌 El video de muestra no se incluye en el repositorio por su tamaño. Colocá tu propio video en `sample_data/` o montá Google Drive.

---

## 🔄 Pipeline de procesamiento

Cada frame del video pasa por las siguientes etapas:

1. **Detección** (`YoloDetector`): YOLOv11 detecta personas (clase 0) con un umbral de confianza configurable.

2. **Tracking** (`ByteTrackTracker`): ByteTrack asigna y mantiene IDs únicos persistentes a lo largo del video, incluso ante oclusiones parciales.

3. **Análisis de ROI** (`OpenCvRoiEngine`): Para cada persona, se toma el punto del pie (centro del borde inferior del bounding box) y se evalúa si está dentro del polígono usando `cv2.pointPolygonTest`.

4. **Gestión de estado** (`InMemoryStateManager`): Registra el historial de posición y estado (dentro/fuera) de cada ID. Detecta cambios de estado y calcula la dirección del movimiento proyectando el vector de movimiento sobre el eje de la escalera.

5. **Motor de eventos** (`DefaultEventEngine`): Convierte los cambios de estado en eventos tipificados:
   - `entered`: La persona ingresó a la ROI
   - `exited`: La persona salió de la ROI
   - `appeared_inside`: La persona fue detectada directamente dentro de la ROI
   
   Incrementa los contadores globales:
   - `contador_suben`: personas que subieron
   - `contador_bajan`: personas que bajaron
   - `contador_roi`: total de ingresos a la ROI

6. **Visualización** (`OpenCvVisualizer`): Dibuja sobre cada frame:
   - El polígono de la ROI en amarillo
   - Bounding boxes en verde (dentro) o rojo (fuera)
   - IDs y etiquetas de eventos
   - Contadores en pantalla: `SUBEN`, `BAJAN`, `TOTAL ROI`

7. **Exportación**: El video anotado se guarda en formato `mp4v` y luego se recodifica a H.264 con FFmpeg para máxima compatibilidad.

---

## 👥 Autores

| Nombre | GitHub |
|---|---|
| Facundo Majda | [@FacundoMajda](https://github.com/FacundoMajda) |
| Marcelo Ortega | [@ortegamarcelodev](https://github.com/ortegamarcelodev) |

---

<div align="center">

**GOTECHY · Grupo 7 · 2026**

*Proyecto de Machine Learning y Visión por Computadora*

</div>
