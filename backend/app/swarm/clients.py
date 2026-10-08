"""Fábrica de clientes de chat: Foundry (live) o simulado (mock)."""

from functools import lru_cache

from agent_framework import BaseChatClient

from ..config import Settings
from .mock import MockChatClient


def model_for(agent: str, settings: Settings) -> str:
    return getattr(settings, f"model_{agent}")


@lru_cache
def _credential():
    from azure.identity.aio import DefaultAzureCredential

    return DefaultAzureCredential()


def make_client(agent: str, settings: Settings) -> BaseChatClient:
    model = model_for(agent, settings)
    if settings.demo_mode == "mock":
        return MockChatClient(agent, model, speed=settings.mock_speed)
    if not settings.foundry_project_endpoint:
        raise RuntimeError("FOUNDRY_PROJECT_ENDPOINT no está configurado (o usa DEMO_MODE=mock)")
    from agent_framework.foundry import FoundryChatClient

    # Responses API vía el proyecto de Foundry: agentes "efímeros" definidos en código.
    return FoundryChatClient(
        project_endpoint=settings.foundry_project_endpoint,
        model=model,
        credential=_credential(),
    )
