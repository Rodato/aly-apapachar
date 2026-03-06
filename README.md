# Aly Apapachar

Bot de WhatsApp especializado en el **Manual A+P (ICBF)** de Equimundo.

Fork minimalista de puddleAsistant — solo RAG, solo un documento.

## Estructura

```
Aly_Apapachar/
├── bot.py              # WhatsApp bot (puerto 8003)
├── orchestrator.py     # Flujo: Language → Intent → RAG
├── console.py          # Testing local sin WhatsApp
├── language_detector.py
├── agents/
│   ├── base_agent.py
│   ├── language_agent.py
│   ├── intent_agent.py   # Solo: GREETING | SENSITIVE | FACTUAL
│   └── rag_agent.py      # Filtrado a "3. MANUAL A+P_vICBF"
├── config/
│   └── welcome_messages.py
├── .env                # Copiar de puddleAsistant y editar
└── requirements.txt
```

## Setup

```bash
cd /Users/daniel/Desktop/Dev/Aly_Apapachar

# 1. Copiar .env de puddleAsistant y editar TWILIO_WHATSAPP_NUMBER
cp ../puddleAsistant/.env .env
# Editar: TWILIO_WHATSAPP_NUMBER=whatsapp:+<nuevo_numero>

# 2. Instalar dependencias (usa el venv de puddleAsistant o crea uno nuevo)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Test local
python3 console.py

# 4. WhatsApp bot
python3 bot.py
```

## Iniciar el bot (producción)

```bash
# Terminal 1
source venv/bin/activate
python3 bot.py

# Terminal 2
ngrok http 8003
# Configurar en Twilio: https://xxxxx.ngrok.io/webhook/whatsapp
```

## Variables de entorno (.env)

```bash
TWILIO_ACCOUNT_SID=<account_sid>
TWILIO_AUTH_TOKEN=<auth_token>
TWILIO_WHATSAPP_NUMBER=whatsapp:+<nuevo_numero_apapachar>

OPENROUTER_API_KEY=<key>
OPENAI_API_KEY=<key>

MONGODB_URI=<connection_string>
MONGODB_DB_NAME=<db_name>
MONGODB_COLLECTION_NAME=<collection_name>
```

## Diferencias con puddleAsistant

| Feature | puddleAsistant | Aly Apapachar |
|---------|---------------|----------------|
| Documentos | 36 documentos | Solo Manual A+P |
| Agentes | RAG + Workshop + Brainstorming | Solo RAG |
| Intents | GREETING/FACTUAL/PLAN/IDEATE/SENSITIVE/AMBIGUOUS | GREETING/FACTUAL/SENSITIVE |
| Puerto | 8002 | 8003 |
| Memoria Supabase | ✅ | ❌ (puede agregarse) |
