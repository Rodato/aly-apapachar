# CLAUDE.md - Aly

## 🎯 Estado Actual del Proyecto

**Proyecto**: Aly — Asistente WhatsApp de Equimundo
**Fecha creación**: 2026-03-05
**Fase**: FUNCIONAL EN LOCAL — pendiente deploy en producción

## 🏗️ Arquitectura del Sistema

- **Aly**: Asistente experta en programas de Equimundo. Ayuda a facilitadores a implementar y aplicar los programas de Equimundo.
- **MongoDB**: Cluster puddle — 3 colecciones: `apapachar`, `aly_general_knowledge`, `user_profiles`
- **WhatsApp**: Twilio — número dedicado
- **Sin Supabase**: Sin memoria conversacional por ahora
- **Idioma**: Solo español por ahora

### Flujo:
```
Usuario → bot.py (check onboarding)
  → Nuevo: OnboardingAgent (nombre → género → país → región → email)
  → Completo: Language Agent → [Intent Agent + Librarian Agent en paralelo] → barrier → Agente → Respuesta
```

### Intents:
`GREETING | FACTUAL | PLAN | IDEATE | SENSITIVE`

### Routing (LibrarianAgent):
- Corre en **paralelo** con el Intent Agent (LangGraph fan-out)
- Colombia → LLM decide colecciones + filtros `theme_category`: `["apapachar"]` | `["aly_general_knowledge"]` | ambas
- No-Colombia → siempre `["aly_general_knowledge"]`, sin filtros

### Filtros de metadata (rag_filters):
- Solo aplica a `aly_general_knowledge` · campo `theme_category`
- Categorías indexadas: `marco_teorico` | `tips_facilitadores` | `mejores_practicas` | `rompehielos`
- Si el filtro retorna 0 docs → fallback sin filtro automático (en `multi_collection_rag.py`)

## 📁 Estructura del Proyecto

```
Aly_Apapachar/
├── bot.py                    # WhatsApp bot (puerto 8003) — check onboarding antes del grafo
├── orchestrator.py           # LangGraph: Language → [Intent ∥ Librarian] → barrier → Agente
├── console.py                # Testing local sin WhatsApp
├── agents/
│   ├── base_agent.py         # AgentState: incluye sources_to_query, rag_filters
│   ├── language_agent.py
│   ├── intent_agent.py       # GREETING | FACTUAL | PLAN | IDEATE | SENSITIVE
│   ├── librarian_agent.py    # Paralelo al Intent — decide colecciones + rag_filters
│   ├── onboarding_agent.py   # Registro stateless de nuevos facilitadores
│   ├── factual_agent.py      # intent: FACTUAL (antes rag_agent.py)
│   ├── plan_agent.py         # intent: PLAN
│   └── ideate_agent.py       # intent: IDEATE
├── rag/
│   ├── simple_rag_mongo.py   # Mantener (backward compat)
│   └── multi_collection_rag.py  # search_chunks(metadata_filters=) — filtro MongoDB $in + fallback
├── db/
│   └── user_profiles.py      # CRUD de perfiles de facilitadores
├── data/
│   ├── ALY_Knowledge_Base.xlsx  # Catálogo completo — fuente del prompt del Librarian
│   └── docs/                 # 22 .docx ingestados en aly_general_knowledge
├── ingest_general_knowledge.py  # Script one-shot (ya ejecutado)
├── config/
│   └── welcome_messages.py
├── Dockerfile
├── docker-compose.yml
├── .env                      # Variables de entorno (NO commitear)
└── requirements.txt
```

## ⚙️ Variables de Entorno (.env)

```bash
TWILIO_ACCOUNT_SID=<account_sid>
TWILIO_AUTH_TOKEN=<auth_token>
TWILIO_WHATSAPP_NUMBER=whatsapp:+<numero>

OPENROUTER_API_KEY=<key>
OPENAI_API_KEY=<key>

MONGODB_URI=<connection_string>
MONGODB_DB_NAME=puddle
```

## 🚀 Comandos Clave

```bash
cd /Users/daniel/Desktop/Dev/Aly_Apapachar
source venv/bin/activate

# Test local
python3 console.py

# Bot WhatsApp (Terminal 1)
python3 bot.py

# Exponer con ngrok (Terminal 2)
ngrok http 8003
# Webhook Twilio: https://xxxxx.ngrok.io/webhook/whatsapp
```

## 🤖 Agentes y Modelos

| Agente | Rol | Modelo | Via |
|--------|-----|--------|-----|
| Onboarding Agent | Pre-proceso nuevos usuarios | — (lógica Python) | — |
| Language Agent | Detecta idioma | mistralai/ministral-8b-2512 | OpenRouter |
| Intent Agent | Clasifica intent (paralelo al Librarian) | mistralai/ministral-8b-2512 | OpenRouter |
| Librarian Agent | Decide colecciones + rag_filters (paralelo al Intent) | minimax/minimax-m2.7 | OpenRouter |
| Factual Agent | FACTUAL — recupera contexto + genera respuesta factual | gpt-4o-mini | OpenAI |
| Plan Agent | PLAN — recupera contexto + genera plan paso a paso | google/gemini-2.5-flash-lite | OpenRouter |
| Ideate Agent | IDEATE — recupera contexto + genera ideas creativas | mistralai/mistral-small-creative | OpenRouter |

## 🔑 Decisiones de Arquitectura

- **Parallel fan-out**: Intent + Librarian corren simultáneamente tras Language. Se sincronizan en un nodo `barrier` antes del agente de respuesta.
- **Cada agente recupera su propio contexto**: Factual, Plan e Ideate llaman a `search_chunks()` directamente con `sources_to_query` + `rag_filters` del estado.
- **Librarian con catálogo completo**: el prompt del Librarian incluye los 22 documentos de la biblioteca con sus resúmenes reales (fuente: ALY_Knowledge_Base.xlsx).
- **rag_agent.py renombrado a factual_agent.py**: clase `FactualAgent`. El nombre refleja el rol, no la técnica.

## 📋 Pendiente

1. **Deploy** en VPS (Hetzner CX22) con Docker Compose + nginx + certbot
2. **Configurar webhook** en Twilio con URL pública
3. **Probar onboarding completo** en WhatsApp real
4. **Opcional**: Soporte EN/PT en prompts (mayo 2026)
5. **Opcional**: Semillas México en colección propia (julio 2026)
