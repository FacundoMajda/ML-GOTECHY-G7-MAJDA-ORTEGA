import json
import urllib.request
import urllib.error
import os

api_key = os.environ.get("COHERE_API_KEY")


SYSTEM_PROMPT = (
    "Sos un asistente experto en analisis de video con inteligencia artificial "
    "especializado en el sistema Argus Vision. Argus Vision es una plataforma de "
    "analisis de video que utiliza deteccion de objetos con YOLO, tracking con "
    "ByteTrack y logica de regiones de interes (ROIs) para contar entradas, salidas, "
    "ocupacion y tiempo de permanencia de personas y objetos en areas definidas.\n\n"
    "Tenes acceso a los datos completos de un analisis (reporte) que incluye:\n"
    "- Informacion de la sesion: fuente de video, fecha, duracion, estado.\n"
    "- Metricas por area (ROI): entradas, salidas, ocupacion maxima, promedio de permanencia.\n"
    "- Datos de entidades rastreadas: IDs de track, primer/ultimo frame visto.\n"
    "- Eventos de zona: entradas y salidas con timestamps, track IDs, numeros de frame.\n"
    "- Snapshots de ocupacion: cuantas entidades estaban dentro/fuera de cada area en distintos momentos.\n\n"
    "Responde preguntas sobre estos datos de forma clara y precisa en español (Argentina). "
    "Si te pasan datos de un analisis, podes resumirlos, comparar areas, "
    "identificar patrones, calcular promedios, o dar recomendaciones basadas en los resultados."
)


def ask_cohere(
    report_data: dict,
    question: str,
    model: str = "command-a-plus-05-2026",
    temperature: float = 0.6,
) -> str:
    if not api_key:
        raise RuntimeError("COHERE_API_KEY no configurada en el entorno")
    report_json = json.dumps(report_data, default=str, indent=2)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Estos son los datos de un analisis de Argus Vision:\n\n"
                f"{report_json}\n\n"
                f"Pregunta: {question}"
            ),
        },
    ]
    body = json.dumps({
        "thinking": {"type": "enabled"},
        "messages": messages,
        "temperature": temperature,
        "model": model,
    }).encode()

    req = urllib.request.Request(
        "https://api.cohere.com/v2/chat",
        data=body,
        headers={
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
        parts = result.get("message", {}).get("content", [])
        for p in parts:
            if p.get("type") == "text":
                return p.get("text", str(result))
        return parts[-1].get("text", str(result)) if parts else str(result)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode(errors="replace")
        raise RuntimeError(f"Cohere API error {e.code}: {error_body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Cohere connection error: {e.reason}") from e
