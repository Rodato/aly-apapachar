"""
LibrarianAgent — decide qué colecciones y categorías consultar basado en la query y el perfil del usuario.

Regla de negocio (hard-coded, NO delegada al LLM):
- Si el país del usuario NO es Colombia → solo "aly_general_knowledge"
  (Semillas México pendiente hasta julio 2026)
- Si el país es Colombia → LLM decide entre:
    ["apapachar"], ["aly_general_knowledge"] o ["apapachar", "aly_general_knowledge"]
  y además elige los filtros de theme_category para aly_general_knowledge.
- Fallback si LLM falla: ambas colecciones, sin filtros
"""

import os
import json
import logging

import requests
from dotenv import load_dotenv

from agents.base_agent import BaseAgent, AgentState

load_dotenv()
logger = logging.getLogger(__name__)

ALL_COLLECTIONS = ["apapachar", "aly_general_knowledge"]
FALLBACK_COLLECTIONS = ALL_COLLECTIONS

VALID_CATEGORIES = [
    "marco_teorico",
    "tips_facilitadores",
    "mejores_practicas",
    "rompehielos",
]

# ---------------------------------------------------------------------------
# Catálogo completo de la biblioteca — base del prompt del Librarian
# Fuente: data/ALY_Knowledge_Base.xlsx (solo documentos con status=Available)
# ---------------------------------------------------------------------------

LIBRARY_CATALOG = """
## COLECCIÓN: apapachar
Manual completo del programa Apapáchar (A+P) del ICBF Colombia.
Cubre: actividades de sesiones, objetivos del programa, metodología A+P, guías paso a paso
para sesiones con padres, madres y cuidadores.
⚠ No soporta filtros de metadata — se busca en el manual completo.

---

## COLECCIÓN: aly_general_knowledge
Conocimiento general de Equimundo. 22 documentos organizados en 4 categorías:

### Categoría: marco_teorico
Conceptos teóricos sobre masculinidades, género, VBG, paternidad y primera infancia.

- doc_tema1_01_glosario_masculinidades
  Glosario de términos clave: sexo, género, normas sociales, masculinidades, VBG.
  Factores de riesgo a nivel individual, relacional, comunitario e institucional.

- doc_tema1_02_enfoques_transformadores_programa_p
  Enfoques transformadores de género para involucrar hombres. Programa P: paternidades
  no violentas y corresponsables. Pautas para sostener participación activa.

- doc_tema1_03_mfs_muchas_formas_ser
  MFS (Muchas Formas de Ser): currículo para jóvenes sobre equidad de género, relaciones
  saludables y prácticas sexuales más seguras. Teoría y principios.

- doc_tema1_04_modulo1_why_engage [ENG]
  Por qué involucrar a hombres y jóvenes. Justificación e introducción al involucramiento
  masculino en igualdad de género.

- doc_tema1_05_modulo2_unpacking_masculinities [ENG]
  Explorando masculinidades. La "Caja de la Masculinidad": cómo las normas rígidas de
  género se construyen socialmente. Reflexión sobre experiencias personales.

- doc_tema1_06_modulo5_equimundo_programas [ENG]
  Familias de programas de Equimundo y cómo adaptarlos e integrarlos a sistemas
  existentes para avanzar en igualdad de género.

- doc_tema1_07_che_ru_padres_masculinidades
  CHe Ru / Programa P (Paraguay): involucrar a padres en gestación, parto y primer año
  de crianza. Educación popular e igualdad entre hombres y mujeres.

- doc_tema1_08_ecd_involucramiento_masculino
  Involucramiento masculino en el cuidado para el desarrollo de la primera infancia (ECD).
  Evidencia, estrategias, buenas prácticas y recomendaciones de política.

- doc_tema1_09_brief1_crianza_reduccion_violencia
  Evidencia sobre cómo los programas de crianza reducen violencia contra niños/as (VAC)
  y mujeres (VAW). Enfoques efectivos para relaciones familiares más seguras.

- doc_tema1_10_brief2_crianza_enfoque_transformador
  Programas de crianza con enfoque transformador de género. Principios, características
  y estrategias para cuestionar normas de género y reducir violencia.

### Categoría: tips_facilitadores
Guías prácticas para facilitar sesiones: preparación, espacios seguros, manejo de situaciones.

- doc_tema2_01_modulo6_comunidad_investigacion [ENG]
  Investigación formativa para diseñar programas relevantes. Comprensión de necesidades
  comunitarias. Guía de adaptación, reclutamiento y gestión de riesgos.

- doc_tema2_02_bonus_preparacion_facilitadores [ENG]
  Rol del/la facilitador/a. Cómo la preparación, habilidades y autoconsciencia permiten
  crear espacios seguros, inclusivos y transformadores.

- doc_tema2_03_mfs_lenguaje_inclusivo_facilitacion
  Uso de lenguaje inclusivo en facilitación (español). Diversidad de identidades de
  género. Cómo facilitar sesiones MFS.

- doc_tema2_04_che_ru_pautas_facilitacion
  Pautas para convocar participantes. Rol del/la facilitador/a en educación popular.
  Manejo de revelaciones de violencia y casos de derivación. Equipos de facilitación.

- doc_tema2_05_ecd_involucramiento_estrategias
  Estrategias para promover involucramiento masculino. Grupos solo hombres vs. mixtos.
  Outreach. Trabajando con comunidades y líderes.

### Categoría: mejores_practicas
Estrategias para diseñar, adaptar, escalar y sostener programas de género con hombres.

- doc_tema3_01_modulo3_estrategias_engagement [ENG]
  Estrategias para involucrar hombres y jóvenes. Cómo escalar programas de manera
  estratégica sin comprometer calidad ni principios transformadores.

- doc_tema3_02_modulo4_preparacion_organizacional [ENG]
  Preparación individual y organizacional para diseñar programas. Importancia de
  procesos reflexivos para lograr cambio sostenible.

- doc_tema3_03_modulo7_diseno_adaptacion [ENG]
  Diseño y adaptación sistemática de programas basada en evidencia. Relevancia local
  y enfoque transformador de género.

- doc_tema3_04_modulo8_atrayendo_interes [ENG]
  Cómo atraer y mantener participación. Estrategias basadas en confianza y comunidad.
  Anticipar y gestionar resistencias.

- doc_tema3_05_modulo11_escalamiento [ENG]
  Expandiendo programas a nuevos contextos manteniendo efectividad, sostenibilidad y
  coherencia con el enfoque transformador.

- doc_tema3_06_hombres_aliados_errores_comunes
  Hoja de ruta para hombres aliados (Equimundo). Errores comunes y enfoques prometedores
  para involucrar hombres en programas de género.

### Categoría: rompehielos
Dinámicas participativas para el inicio y activación de sesiones.

- doc_tema4_01_rompehielos_dinamicas
  Rompehielos y energizadores: movimiento, juego y conexión interpersonal. Generan
  confianza y ambiente seguro para sesiones sobre masculinidades, género e igualdad.
"""


class LibrarianAgent(BaseAgent):

    def __init__(self):
        super().__init__("LibrarianAgent", "Decide qué colecciones y categorías consultar según la query y el país del usuario")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_key:
            raise ValueError("OPENROUTER_API_KEY no encontrada")
        self.headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
        }
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "minimax/minimax-m2.7"
        logger.info("✅ Librarian Agent inicializado")

    def process(self, state: AgentState) -> AgentState:
        country = (state.user_profile or {}).get("country", "")

        # Hard rule: non-Colombia users only get general knowledge (no metadata filter)
        if country != "colombia":
            logger.info(f"🗺️  País={country!r} → solo aly_general_knowledge")
            state.sources_to_query = ["aly_general_knowledge"]
            state.rag_filters = None
            return state

        # Colombia users: LLM decides collections + metadata filters
        result = self._decide_for_colombia(state.user_input)
        logger.info(f"📚 Librarian → {result['collections']} | filtros={result['metadata_filters']}")
        state.sources_to_query = result["collections"]
        state.rag_filters = result["metadata_filters"] or None
        return state

    def _decide_for_colombia(self, query: str) -> dict:
        prompt = f"""Eres el bibliotecario experto de Aly, asistente de Equimundo.
Tu única tarea es decidir qué fuentes de conocimiento recuperar para responder la siguiente pregunta de un facilitador.

---
{LIBRARY_CATALOG}
---

## PREGUNTA DEL FACILITADOR
"{query}"

## TU TAREA

1. Decide qué colección(es) consultar:
   - "apapachar": si la pregunta es sobre actividades, sesiones, metodología o el manual Apapáchar Colombia.
   - "aly_general_knowledge": si es sobre teoría, masculinidades, facilitación, mejores prácticas o rompehielos.
   - Ambas: si la pregunta necesita tanto el manual específico como el conocimiento general.

2. Si usas "aly_general_knowledge", decide qué categorías son relevantes (puedes elegir varias o ninguna):
   - "marco_teorico": conceptos de masculinidades, género, VBG, paternidad, evidencia.
   - "tips_facilitadores": cómo facilitar, preparación, espacios seguros, manejo de revelaciones.
   - "mejores_practicas": diseño/adaptación de programas, engagement, escalamiento.
   - "rompehielos": dinámicas de inicio, energizadores, activaciones.
   Si la pregunta es amplia y puede abarcar varias categorías, omite el filtro (deja metadata_filters vacío).

## RESPUESTA
Responde SOLO con JSON válido, sin texto adicional:
{{
  "collections": ["apapachar"],
  "metadata_filters": {{}},
  "reasoning": "breve justificación"
}}

Ejemplos de valores válidos para collections:
- ["apapachar"]
- ["aly_general_knowledge"]
- ["apapachar", "aly_general_knowledge"]

Ejemplo con filtro de categoría:
{{
  "collections": ["aly_general_knowledge"],
  "metadata_filters": {{
    "aly_general_knowledge": {{"theme_category": ["rompehielos"]}}
  }},
  "reasoning": "pregunta sobre dinámicas de inicio"
}}"""

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0.1,
                },
                timeout=20,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            return self._parse_result(content)
        except Exception as e:
            logger.error(f"LibrarianAgent LLM error: {e} — using fallback")
            return {"collections": FALLBACK_COLLECTIONS, "metadata_filters": None}

    def _parse_result(self, response: str) -> dict:
        valid_cols = set(ALL_COLLECTIONS)
        valid_cats = set(VALID_CATEGORIES)
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                parsed = json.loads(response[start:end])

                cols = [c for c in parsed.get("collections", []) if c in valid_cols]
                if not cols:
                    cols = FALLBACK_COLLECTIONS

                raw_filters = parsed.get("metadata_filters") or {}
                metadata_filters = {}
                if "aly_general_knowledge" in raw_filters:
                    cats = raw_filters["aly_general_knowledge"].get("theme_category", [])
                    valid_selected = [c for c in cats if c in valid_cats]
                    if valid_selected:
                        metadata_filters["aly_general_knowledge"] = {"theme_category": valid_selected}

                return {"collections": cols, "metadata_filters": metadata_filters or None}
        except Exception:
            pass
        logger.warning(f"Could not parse librarian response: {response!r} — fallback")
        return {"collections": FALLBACK_COLLECTIONS, "metadata_filters": None}
