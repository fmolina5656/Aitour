"""Crea (o versiona) el voice agent recepcionista en el proyecto de Foundry.

Uso:  cd backend && .venv/bin/python -m scripts.create_voice_agent
Requiere FOUNDRY_PROJECT_ENDPOINT en .env y `az login` (o Managed Identity) con rol Foundry User.
"""

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from app.config import get_settings
from app.voice.definition import build_definition


def main() -> None:
    s = get_settings()
    if not s.foundry_project_endpoint:
        raise SystemExit("Falta FOUNDRY_PROJECT_ENDPOINT en .env")
    definition = build_definition(s)
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=s.foundry_project_endpoint, credential=credential, allow_preview=True) as client,
    ):
        created = client.agents.create_version(agent_name=s.voice_agent_name, definition=definition)
        print(f"Voice agent '{s.voice_agent_name}' versión {created.version} creado.")
        print(f"Para fijar esta versión en la demo: VOICE_AGENT_VERSION={created.version}")


if __name__ == "__main__":
    main()
