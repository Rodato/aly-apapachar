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

## 📝 Conversation Closer Prompt (TESTEADO ✅)

Prompt para el sistema que analiza transcripciones y genera resumen + keywords + flags + razonamiento.

**Decisiones tomadas:**
- Campo: `keywords` (no `concepts`) — el dashboard de Supabase lo espera así en `conversations_data.keywords`
- `flags`: string CSV (no array) — formato `"general-inquiry, needs-followup"`
- `flag_reasoning`: campo adicional para debugging/revisión humana — no está en el schema de producción de Supabase aún
- Flags son leídas por un humano, no por lógica automática. El prefijo LOW/MEDIUM/HIGH orienta la atención.
- Modelo: `google/gemini-2.5-flash` vía OpenRouter — mejor que gpt-4o-mini para esta tarea
- Script de testing: `test_conversation_closer.py` — genera Excel con severidad, transcripción, summary, keywords, flags y reasoning

**Prompt de producción:**
```
You are a conversation analyst for Aly, an AI assistant supporting facilitators of Equimundo programs.

Given a conversation transcript, generate a JSON object with:

1. "summary": A specific, informative summary in the SAME LANGUAGE as the transcript (3-5 sentences). Cover: what the facilitator was trying to accomplish, the main content exchanged, any concerning statements or disclosures made (by the facilitator or about participants), and how the conversation ended.

2. "keywords": A comma-separated list of key concepts, themes, and topics discussed (3-8 items), in the SAME LANGUAGE as the transcript. Include program names, facilitation topics, types of activities, or issues raised — not just surface-level keywords.

3. "flags": A comma-separated string of applicable flags. Choose only from the following:

Risk flags (use when harmful content is present — prefix indicates severity):
- LOW-normative-harm: sexist jokes, harmful stereotypes, dismissive comments about gender or consent
- LOW-minimization: minimizing, excusing, or joking about harmful behavior
- MEDIUM-coercive-control: restricting a partner's movement, communication, or social connections
- MEDIUM-economic-control: restricting or monitoring a partner's access to money
- MEDIUM-psychological-abuse: insults, humiliation, intimidation, emotional manipulation
- MEDIUM-repeated-disruption: persistent harmful commentary or intentional disruption
- HIGH-physical-violence: admission or threat of physical violence
- HIGH-sexual-coercion: non-consensual sex, pressure for sex, or disregard for consent
- HIGH-stalking-threats: stalking, obsessive pursuit, or escalating contact after separation
- HIGH-imminent-danger: signs of immediate risk to self or others
- HIGH-loss-of-control: person expresses fear of hurting someone or losing control

Operational flags (always applicable when relevant):
- needs-followup: conversation requires human review or follow-up
- emotional-distress: facilitator or participant showing signs of emotional distress
- shared-personal-info: sensitive personal information was disclosed
- asked-about-resources: asked about support resources, referrals, or external help
- facilitation-challenge: facilitator is struggling with a specific implementation issue
- general-inquiry: routine information request, no concerning content

Respond ONLY with valid JSON, no other text. "flags" must always be a comma-separated string, never an array.

Transcript:
{transcription}
```

## 📋 Pendiente

1. **Deploy** en VPS (Hetzner CX22) con Docker Compose + nginx + certbot
2. **Configurar webhook** en Twilio con URL pública
3. **Probar onboarding completo** en WhatsApp real
4. **Opcional**: Soporte EN/PT en prompts (mayo 2026)
5. **Opcional**: Semillas México en colección propia (julio 2026)

## 🔗 Proyecto Complementario: Aly_dashboard

**Ubicación**: `/Users/daniel/Desktop/Dev/Aly_dashboard/`

El dashboard es el frontend analítico de este bot. Lee de **Supabase** (PostgreSQL), no de MongoDB.

### Flujo de datos entre proyectos
```
Aly_Apapachar (bot) → Conversation Closer → Supabase → Aly_dashboard
```

### Contrato de datos crítico
El Conversation Closer de **este proyecto** alimenta las tablas que el dashboard consume:
- `conversations_data.keywords` — string CSV (no array). El dashboard lo parsea para la página de keywords.
- `conversations_data.flags` — string CSV con prefijos LOW/MEDIUM/HIGH. El dashboard los clasifica en 🔴/🟠 en la página de alertas.
- `conversations_data.summary` — texto libre. Dashboard lo muestra en la página de conversaciones.

**Si cambiás el formato de keywords o flags aquí, actualizá el parser en `Aly_dashboard/pages/conversaciones.py` y `alertas.py`.**

### Tablas Supabase que consume el dashboard
| Tabla | Quién escribe |
|---|---|
| `public.users_interactions` | bot.py (cada mensaje) |
| `public.users_data` | onboarding_agent.py (registro) |
| `public.conversations_data` | Conversation Closer (al cerrar sesión) |
| `vector_aly.rag_embeddings` | ingest scripts |

---

## ✅ Sesión 2026-04-06

### Sensitive Agent — IMPLEMENTADO (pendiente testeo)

**`agents/sensitive_agent.py`** — nuevo agente LLM, sin RAG.
- Modelo: `google/gemini-2.5-flash` vía OpenRouter, temperatura 0.3
- Prompt basado en `data/Aly Flagging, Escalation, and Response Protocol.md`
- Estructura de respuesta: Acknowledge → Name the concern → Set boundary → Encourage safer action
- Sin "route to human" por ahora — se agrega después del testeo
- Fallback: `get_sensitive_message()` del archivo estático si el LLM falla
- Orquestador actualizado: `_sensitive_node` ya llama al agente real

**Intent Agent actualizado** — prompt mejorado en 3 idiomas:
- SENSITIVE = facilitador REPORTANDO o VIVIENDO algo (angustia, disclosure de violencia, crisis activa)
- FACTUAL/PLAN/IDEATE = pide información o herramientas, aunque el tema sea difícil
- El diferenciador NO es el tema sino si necesita contención vs. información

**Criterio clave de routing**:
- Los flags operacionales (`emotional-distress`, etc.) se aplican a TODAS las conversaciones → no son señal confiable para routing en tiempo real
- El routing SENSITIVE se basa en el contenido del mensaje individual

## 🔜 Próxima sesión

- **Testear Sensitive Agent** con `console.py` usando casos del protocolo: LOW (chiste sexista), MEDIUM (control social/económico), HIGH (violencia física, pérdida de control)
- Evaluar si la respuesta es apropiadamente corta y sigue la estructura del protocolo
- Decidir si agregar "route to human" según resultado del testeo

---

## 🔜 Lunes 2026-04-27 — Retomar LangSmith Fase 1

**Dónde quedamos (sesión 2026-04-22):**

Plan completo en `~/.claude/projects/-Users-daniel-Desktop-Dev-Aly-Apapachar/memory/project_langsmith_roadmap.md`

### ✅ Paso 1 — Saved Filters (COMPLETADO)
5 filtros guardados en LangSmith proyecto `aly-apapachar-prod`:
1. `Slow conversations (>=5s)` — vista Traces
2. `Errors` — vista Traces
3. `Intent distribution` — vista Runs, filter: `Name = classifyIntent`
4. `Triage SENSITIVE` — vista Runs, filter: `Name = triage` AND `Output contains true`
5. `Librarian routing` — vista Runs, filter: `Name = librarian`

### ⏸️ Paso 2 — Monitor tab (PAUSADO — retomar después del Paso 3)
Pendiente configurar charts p50/p95, tokens, intent distribution.

### 🔜 Paso 3 — Annotation Queue "Aly - Review Semanal" (DONDE RETOMAMOS EL LUNES)

Crear queue en LangSmith → Annotation Queues con:

**Rúbrica de anotación:**
| Campo | Tipo | Opciones |
|---|---|---|
| `correct_response` | boolean | 👍 / 👎 |
| `issue_type` | categórico | hallucination, wrong_intent, wrong_routing, bad_format, tone_off, triage_miss, other, none |
| `severity` | categórico | low, medium, high |
| `notes` | texto libre | razonamiento |

**Reglas de auto-añadir (automation rules):**
- **A**: `Name=triage` AND `Output contains true` → 100% sampling (TODOS los SENSITIVE)
- **B**: `Is root run=true` AND `Latency > 8s` → 100% sampling
- **C**: `Is root run=true` → 2% sampling aleatorio (baseline)
- **D**: `Name=triage` AND `Output contains false` → 2% sampling (auditar falsos negativos)

### 🔎 Hallazgos importantes de la sesión (para revisar el lunes)

1. **Ideate Agent = cuello de botella** — `mistralai/mistral-small-creative` tarda ~8.27s con ~5,102 tokens. Comparado con Plan (gemini-2.5-flash-lite) que hace 3,387 tokens en 1.52s. Candidato a swap por `google/gemini-2.5-flash` o `anthropic/claude-haiku-4-5`. **Detalle en `project_ideate_latency.md`**.

2. **Triage false-negatives** — en 1 día de tráfico, 100% de triages dieron `false`. Puede ser real (no hay casos sensibles) o falsos negativos (caso más peligroso). **Acordamos automatizar esto como evaluador LLM-as-judge en Fase 2** — es el evaluador más crítico.

3. **Nodos duplicados aparentes** (`classifyIntent` + `classify_intent`, `triage` padre + `triage` hijo) = **no son bug**, es anidación natural de LangGraph (wrapper del nodo + función interna). Ignorable.

### 📅 Fases siguientes

- **Semana 2026-04-29**: Fase 2 — Datasets + Evaluadores LLM-as-judge (Factual/Plan/Ideate/Sensitive/Triage-false-negatives)
- **Inicios/mediados mayo 2026**: Fase 3 — Alertas proactivas (webhooks de error rate, latencia, SENSITIVE real-time)

---

## ✅ Sesión 2026-04-30 — MVP Refinado (Python freeze)

Producción TS vive en `../Aly` (repo `Estudio-Plural/Aly`). Este repo Python queda como MVP archivado en `Rodato/aly-apapachar`.

### Cambios aplicados (alta + media prioridad del backlog)

**Modelos:**
- Ideate Agent: `mistralai/mistral-small-creative` → `google/gemini-2.5-flash` (resuelve cuello de botella de latencia documentado en `project_ideate_latency.md`).

**Arquitectura de prompts:**
- Todos los agentes de respuesta (Factual, Plan, Ideate, Sensitive) ahora usan `role:system` + `role:user` separados.
- Cap explícito de longitud para WhatsApp: Factual ≤500 tok / Plan ≤600 tok / Ideate ≤700 tok / Sensitive ≤250 tok.

**Prompts:**
- **Intent Agent**: eliminado SENSITIVE (redundante con Triage). Simplificado a 4 intents: GREETING | PLAN | IDEATE | FACTUAL. Few-shot JSON (3 ejemplos) en ES/EN/PT.
- **Sensitive Agent**: dos estructuras de respuesta — LOW/MED (4 oraciones, Acknowledge→Name→Boundary→Encourage) vs HIGH (3 oraciones, Validate→Urgency→Direct to help). Few-shot LOW + HIGH en ES/EN/PT.
- **Plan Agent**: few-shot input→output. Cap WhatsApp explícito.
- **Ideate Agent**: few-shot input→output. Cap WhatsApp explícito.
- **Factual Agent**: prompt movido desde `rag/multi_collection_rag.py` (acoplamiento incorrecto). `MultiCollectionRAG` ahora es solo recuperación; `generate_answer()` y `set_language_config()` eliminados.
- **Librarian Agent**: 6 ejemplos de query→decisión cubriendo cada categoría de routing.

### Items NO ejecutados (baja/arquitectural — backlog futuro si retoman Python)
- 9. Eliminar campo `reasoning` del Librarian (no se usa en runtime)
- 10. Eliminar campo `confidence` del Intent (no se usa)
- 11. Triage — caso borde planificación vs angustia
- 12. Fusionar Language + Intent en una llamada
- 13. (Item 13 ya aplicado: role:system en todos)
