# Aly Apapachar

Bot de WhatsApp especializado en el **Manual A+P (ICBF)** de Equimundo.
Asistente para facilitadores del programa de crianza **Apapáchar** — responde consultas, ayuda a planificar sesiones y genera ideas creativas, todo basado en un único documento fuente.

---

## Arquitectura

```
Usuario
  └── Language Agent        → detecta ES / EN / PT
        └── Intent Agent    → clasifica la intención
              ├── GREETING  → mensaje de bienvenida
              ├── FACTUAL   → RAG Agent
              ├── PLAN      → Plan Agent
              ├── IDEATE    → Ideate Agent
              └── SENSITIVE → mensaje de derivación
```

**Fuente única:** `3. MANUAL A+P_vICBF.docx.md` — filtro hardcodeado en MongoDB.

---

## Agentes y modelos

| Agente | Modelo | Propósito |
|--------|--------|-----------|
| **Language Agent** | `mistralai/ministral-8b-2512` | Detecta el idioma del mensaje (ES/EN/PT) |
| **Intent Agent** | `mistralai/ministral-8b-2512` | Clasifica la intención: GREETING / FACTUAL / PLAN / IDEATE / SENSITIVE |
| **RAG Agent** | `gpt-4o-mini` | Responde preguntas factuales sobre el Manual A+P |
| **Plan Agent** | `google/gemini-2.5-flash-lite` | Ayuda a implementar y adaptar actividades a contextos específicos |
| **Ideate Agent** | `mistralai/mistral-small-creative` | Genera ideas creativas e inspiradoras ancladas en el Manual |

### Intenciones detectadas

| Intent | Cuándo se activa |
|--------|-----------------|
| `GREETING` | El usuario saluda o inicia la conversación |
| `FACTUAL` | Busca información o definiciones del manual |
| `PLAN` | Quiere implementar, adaptar o planificar una actividad concreta |
| `IDEATE` | Pide nuevas ideas, variaciones o inspiración |
| `SENSITIVE` | Tema de trauma, abuso, crisis de salud mental → derivación |

---

## Estructura del proyecto

```
Aly_Apapachar/
├── bot.py                   # WhatsApp bot — FastAPI, puerto 8003
├── orchestrator.py          # Flujo LangGraph: Language → Intent → Agente
├── console.py               # Testing local sin WhatsApp
├── language_detector.py     # Detector de idioma (ES/EN/PT)
├── agents/
│   ├── base_agent.py        # Clase base y AgentState
│   ├── language_agent.py    # Detección de idioma
│   ├── intent_agent.py      # Clasificación de intención
│   ├── rag_agent.py         # Respuestas factuales (RAG)
│   ├── plan_agent.py        # Planificación de actividades
│   └── ideate_agent.py      # Ideación creativa
├── rag/
│   └── simple_rag_mongo.py  # RAG sobre MongoDB (embeddings + cosine similarity)
├── config/
│   └── welcome_messages.py  # Mensajes de bienvenida y follow-up (ES/EN/PT)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Variables de entorno

Crear un archivo `.env` con:

```bash
# Twilio — número dedicado para Apapachar
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=whatsapp:+

# APIs
OPENROUTER_API_KEY=
OPENAI_API_KEY=

# MongoDB (compartido con puddleAsistant)
MONGODB_URI=
MONGODB_DB_NAME=
MONGODB_COLLECTION_NAME=
```

---

## Setup local

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test sin WhatsApp
python3 console.py

# Bot completo
python3 bot.py
# En otra terminal:
ngrok http 8003
# Configurar en Twilio: https://xxxx.ngrok.io/webhook/whatsapp
```

---

## Deploy con Docker

```bash
docker compose up -d

# Logs
docker compose logs -f apapachar

# Actualizar
git pull && docker compose up -d --build
```

El `docker-compose.yml` incluye healthcheck automático sobre `/health`.

---

## Stack técnico

- **Framework:** FastAPI + LangGraph
- **WhatsApp:** Twilio
- **Base de datos:** MongoDB Atlas (búsqueda semántica con cosine similarity)
- **Embeddings:** `text-embedding-ada-002` (OpenAI)
- **LLMs:** OpenRouter + OpenAI
- **Idiomas soportados:** Español, Inglés, Portugués
