"""tracking.py
Módulo de tracking de visitas para aplicaciones Flask.
Llama a track_visit() desde before_request o directamente en cada ruta.
"""

import threading

import requests

_PROYECTO = "Sierra Dron (Inventarios)"
_API_BASE_URL = "http://10.185.36.30:9004"


def track_visit(pagina: str = "", url: str = "", ip_cliente: str = "", user_agent: str = "") -> None:
    """Registra una visita en la API de Analytics (no bloquea el hilo principal)."""

    def _send() -> None:
        try:
            requests.post(
                f"{_API_BASE_URL}/api/v1/analytics/track",
                json={
                    "proyecto": _PROYECTO,
                    "pagina":   pagina or "Inicio",
                    "url":      url,
                    "ip_cliente": ip_cliente,
                    "user_agent": user_agent,
                },
                timeout=2,
            )
        except Exception:
            pass  # El tracking nunca debe interrumpir la app

    threading.Thread(target=_send, daemon=True).start()