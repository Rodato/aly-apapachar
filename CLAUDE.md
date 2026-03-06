# CLAUDE.md - Aly Apapachar

## 🎯 Estado Actual del Proyecto

**Proyecto**: Aly Apapachar - Bot WhatsApp especializado en el Manual A+P (ICBF)
**Fecha creación**: 2026-03-05
**Fase**: PROYECTO CREADO - PENDIENTE ACTIVACIÓN ⏳
**Origen**: Fork minimalista de puddleAsistant

## 🏗️ Arquitectura del Sistema

**Un documento, un agente, un propósito.**

- **MongoDB**: Mismo cluster que puddleAsistant — filtro hardcodeado a `"3. MANUAL A+P_vICBF.docx.md"`
- **WhatsApp**: Twilio — número diferente al bot principal
- **Sin Supabase**: Versión mini sin memoria conversacional (puede agregarse después)

### Flujo simplificado:
```
Usuario → Language Detection → Intent (GREETING | SENSITIVE | FACTUAL) → RAG filtrado → Respuesta
```

## 📁 Estructura del Proyecto

```
Aly_Apapachar/
├── bot.py              # WhatsApp bot (puerto 8003)
├── orchestrator.py     # Orquestador LangGraph simplificado
├── console.py          # Testing local sin WhatsApp
├── language_detector.py
├── agents/
│   ├── base_agent.py
│   ├── language_agent.py
│   ├── intent_agent.py   # Solo: GREETING | SENSITIVE | FACTUAL
│   └── rag_agent.py      # Filtro hardcodeado al Manual A+P
├── config/
│   └── welcome_messages.py  # Mensajes específicos de Apapáchar (ES/EN/PT)
├── .env                # Variables de entorno (NO commitear)
└── requirements.txt
```

## ⚙️ Variables de Entorno (.env)

```bash
# Twilio - número dedicado para Apapachar
TWILIO_ACCOUNT_SID=<account_sid>
TWILIO_AUTH_TOKEN=<auth_token>
TWILIO_WHATSAPP_NUMBER=whatsapp:+<numero_apapachar>

# APIs (mismas que puddleAsistant)
OPENROUTER_API_KEY=<key>
OPENAI_API_KEY=<key>

# MongoDB (mismo cluster que puddleAsistant)
MONGODB_URI=<connection_string>
MONGODB_DB_NAME=<db_name>
MONGODB_COLLECTION_NAME=<collection_name>
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

## 🔧 Setup Inicial (una vez)

```bash
# 1. Copiar .env de puddleAsistant
cp ../puddleAsistant/.env .env
# Editar TWILIO_WHATSAPP_NUMBER al número de Apapachar

# 2. Crear venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Probar
python3 console.py
```

## 🔑 Diferencias vs puddleAsistant

| Feature | puddleAsistant | Aly Apapachar |
|---------|---------------|----------------|
| Documentos | 36 documentos | Solo Manual A+P (ICBF) |
| Agentes | RAG + Workshop + Brainstorming | Solo RAG |
| Intents | 6 (GREETING/FACTUAL/PLAN/IDEATE/SENSITIVE/AMBIGUOUS) | 3 (GREETING/FACTUAL/SENSITIVE) |
| Puerto | 8002 | 8003 |
| Memoria Supabase | ✅ | ❌ (puede agregarse) |
| Filtro MongoDB | Dinámico por programa | Hardcodeado a A+P vICBF |

## 📋 Tareas Pendientes

1. **Copiar y configurar .env** con número de WhatsApp dedicado
2. **Crear venv e instalar dependencias**
3. **Test con `console.py`** antes de conectar WhatsApp
4. **Configurar webhook en Twilio** con URL de ngrok/VPS
5. **Opcional**: Agregar memoria Supabase (copiar de puddleAsistant)
