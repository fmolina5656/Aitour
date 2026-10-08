"""Salidas estructuradas de cada agente.

Todos los campos son requeridos (nullable cuando aplica) para que sean compatibles con
`response_format` estricto de la Responses API.
"""

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Brief(_Strict):
    problema: str
    industria: str
    volumen: str
    datos: str
    empresa: str | None = None

    def as_prompt(self) -> str:
        return (
            f"BRIEF DEL VISITANTE\n- Problema: {self.problema}\n- Industria: {self.industria}\n"
            f"- Volumen: {self.volumen}\n- Datos disponibles: {self.datos}"
        )


class Objecion(_Strict):
    para: str = Field(description="Agente al que se dirige: 'arquitecto'")
    motivo: str
    propuesta: str


class Componente(_Strict):
    id: str = Field(description="identificador corto, snake_case")
    nombre: str = Field(description="etiqueta corta para el diagrama")
    servicio: str = Field(description="clave exacta del catálogo de precios")
    cantidad: float = Field(description="cantidad mensual en la unidad del catálogo")
    supuesto: str = Field(description="supuesto explícito que justifica la cantidad")


class Conexion(_Strict):
    de: str
    a: str
    etiqueta: str


class ArquitectoOut(_Strict):
    burbuja: str = Field(description="máx. 140 caracteres, se lee en pantalla gigante")
    resumen: str
    componentes: list[Componente]
    conexiones: list[Conexion]
    cambios: str | None = Field(description="qué cambió respecto de la versión anterior, o null")


class FinancieroOut(_Strict):
    burbuja: str
    comentario: str
    supuestos: list[str]
    objecion: Objecion | None


class Regulacion(_Strict):
    norma: str
    aplica_por: str


class RiesgoOut(_Strict):
    burbuja: str
    datos_sensibles: list[str]
    regulacion: list[Regulacion]
    mitigaciones: list[str]
    objecion: Objecion | None


class Zona(_Strict):
    nombre: str = Field(description="nombre corto de la zona, p. ej. 'Ingesta', 'Inteligencia', 'Entrega'")
    componentes: list[str] = Field(description="ids de componentes de la arquitectura final, en orden")


class Flujo(_Strict):
    de: str
    a: str
    etiqueta: str = Field(description="máx. 3 palabras: qué viaja por la flecha")


class DiagramadorOut(_Strict):
    burbuja: str
    titulo: str = Field(description="título del diagrama, máx. 60 caracteres")
    zonas: list[Zona] = Field(description="3 o 4 zonas de izquierda a derecha, en el orden del flujo")
    flujo: list[Flujo] = Field(description="flechas numeradas en el orden en que ocurre el proceso")
    pasos: list[str] = Field(description="3 a 5 frases cortas que explican el flujo a un director, en orden")


class RedactorOut(_Strict):
    burbuja: str
    titulo: str
    problema: str
    solucion: str
    beneficios: list[str]
    riesgos_y_mitigaciones: list[str]
    siguientes_pasos: list[str]


OUTPUT_MODELS: dict[str, type[_Strict]] = {
    "arquitecto": ArquitectoOut,
    "financiero": FinancieroOut,
    "riesgo": RiesgoOut,
    "diagramador": DiagramadorOut,
    "redactor": RedactorOut,
}
