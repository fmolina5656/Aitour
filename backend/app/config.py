"""Configuración central. Todo sale de variables de entorno / .env (ver .env.example)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(REPO_DIR / ".env", BACKEND_DIR / ".env"), extra="ignore")

    # live = Foundry real · mock = sin Azure · replay = reproduce una sesión grabada
    demo_mode: Literal["live", "mock", "replay"] = "mock"

    # Microsoft Foundry
    foundry_project_endpoint: str = ""
    model_arquitecto: str = "gpt-5.4"
    model_financiero: str = "gpt-5.4-mini"
    model_riesgo: str = "gpt-5.4-mini"
    model_redactor: str = "gpt-5.4-mini"
    model_guard: str = "gpt-5.4-nano"  # clasificador de tema (rápido y barato)
    reasoning_effort: Literal["none", "low", "medium", "high"] = "low"

    # Voz: Microsoft Foundry voice agent (preview) que hace de recepcionista
    voice_agent_name: str = "readymind-recepcionista"
    voice_agent_version: str = ""  # vacío = versión activa
    voice_model_type: Literal["managed", "self_deployed"] = "managed"
    voice_model: str = "gpt-realtime-2.1"
    voice_name: str = "es-MX-Ximena:DragonHDLatestNeural"  # respaldo: es-MX-DaliaNeural
    voice_vad_threshold: float = 0.6  # más alto = menos falsos disparos por ruido de feria
    voice_rai_policy: str = ""  # nombre del guardrail (RAI policy) para el voice agent
    interview_soft_limit_s: float = 70.0  # a partir de aquí se le pide cerrar la entrevista
    interview_hard_limit_s: float = 95.0  # corte duro: se arma el brief con lo transcrito
    voice_goodbye_s: float = 3.0  # tiempo para la frase de despedida antes de cerrar la voz

    # One-pager, QR y leads
    public_base_url: str = ""  # URL pública (Container Apps) para el QR; vacío = la del request
    lead_secret: str = ""  # firma de los links del QR; vacío = aleatorio por proceso (los QR vencen al reiniciar)
    data_dir: Path = REPO_DIR / "data"  # one-pagers, PDFs y leads (en ACA: volumen de Azure Files)
    chromium_path: str = ""  # vacío = el Chromium de Playwright
    # Envío por mail con Power Automate (disparador HTTP "When an HTTP request is received")
    power_automate_url: str = ""  # vacío = no se envía; los leads quedan en la bandeja de salida
    power_automate_timeout_s: float = 15.0
    max_leads_per_session: int = 3
    # Aviso de privacidad (PENDIENTE: validar con el área legal de Readymind)
    privacy_responsable: str = "Readymind (razón social y domicilio pendientes de validar por el área legal)"
    privacy_contacto: str = "privacidad@readymind.ms (pendiente de confirmar)"
    privacy_aviso_integral: str = "https://www.readymind.ms (pendiente de confirmar la URL del aviso integral)"

    # Gobierno: Prompt Shields (Azure AI Content Safety). Con un recurso de Foundry (AIServices)
    # es el endpoint del recurso: https://<recurso>.cognitiveservices.azure.com
    content_safety_endpoint: str = ""
    guard_timeout_s: float = 4.0
    applicationinsights_connection_string: str = ""
    otel_sensitive_data: bool = False  # no exportar prompts/respuestas de visitantes

    # Presupuestos del enjambre (requisito: < 120 s)
    swarm_timeout_s: float = 110.0  # corte interno, con margen
    display_budget_s: int = 120  # lo que ve el público
    turn_idle_timeout_s: float = 25.0
    swarm_max_rounds: int = 9
    max_debate_rounds: int = 2

    # Reglas que disparan la objeción del Financiero
    objection_component_share: float = 0.40
    objection_monthly_budget_usd: float = 6000.0

    # Mock: multiplicador de latencias simuladas (0 = instantáneo, útil en tests)
    mock_speed: float = 1.0

    # Si Foundry falla antes de que hable algún agente, se reproduce una sesión grabada (modo live)
    auto_failover: bool = True

    # Grabaciones
    recordings_dir: Path = REPO_DIR / "recordings"
    replay_file: str = ""  # vacío = la grabación curada más reciente

    pricing_dir: Path = BACKEND_DIR / "pricing"
    knowledge_dir: Path = BACKEND_DIR / "knowledge"
    frontend_dist: Path = REPO_DIR / "frontend" / "dist"


@lru_cache
def get_settings() -> Settings:
    return Settings()
