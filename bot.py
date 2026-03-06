#!/usr/bin/env python3
"""
Aly Apapachar - WhatsApp Bot
Bot especializado en el Manual A+P (ICBF) de Equimundo.
Puerto: 8003
"""

import os
import sys
import asyncio
import logging
import concurrent.futures
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from twilio.rest import Client
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

load_dotenv(os.path.join(current_dir, '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Aly Apapachar - WhatsApp Bot")

orchestrator = None
twilio_client: Optional[Client] = None
executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)

MAX_MSG_LENGTH = 1000


def init_orchestrator():
    try:
        from orchestrator import ApapacharOrchestrator
        logger.info("🚀 Inicializando Apapachar Orchestrator...")
        return ApapacharOrchestrator()
    except Exception as e:
        logger.error(f"❌ Error inicializando orchestrator: {e}")
        return None


@app.on_event("startup")
async def startup_event():
    global orchestrator, twilio_client

    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')

    if not account_sid or not auth_token:
        logger.error("❌ Faltan TWILIO_ACCOUNT_SID o TWILIO_AUTH_TOKEN en .env")
    else:
        twilio_client = Client(account_sid, auth_token)
        logger.info("✅ Cliente Twilio inicializado")

    loop = asyncio.get_event_loop()
    orchestrator = await loop.run_in_executor(executor, init_orchestrator)

    if orchestrator:
        logger.info("✅ Aly Apapachar lista")
    else:
        logger.warning("⚠️ Orchestrator no disponible - modo básico")


def clean_for_whatsapp(text: str) -> str:
    """Limpia formato markdown para WhatsApp."""
    return text.replace('**', '').replace('##', '').replace('###', '').replace('- ', '• ').strip()


def split_message(text: str, max_length: int = MAX_MSG_LENGTH) -> list:
    """
    Divide texto largo en partes de max_length caracteres,
    cortando en saltos de párrafo, línea o espacio (nunca en medio de una palabra).
    """
    if len(text) <= max_length:
        return [text]

    parts = []
    while len(text) > max_length:
        cut = text.rfind('\n\n', 0, max_length)
        if cut == -1:
            cut = text.rfind('\n', 0, max_length)
        if cut == -1:
            cut = text.rfind(' ', 0, max_length)
        if cut == -1:
            cut = max_length

        parts.append(text[:cut].strip())
        text = text[cut:].strip()

    if text:
        parts.append(text)

    return parts


async def send_whatsapp(to_number: str, whatsapp_number: str, text: str):
    """Envía un texto como uno o varios mensajes WhatsApp según su longitud."""
    cleaned = clean_for_whatsapp(text)
    parts = split_message(cleaned)

    for i, part in enumerate(parts):
        twilio_client.messages.create(body=part, from_=whatsapp_number, to=to_number)
        if len(parts) > 1:
            logger.info(f"📤 Parte {i+1}/{len(parts)} enviada ({len(part)} chars)")


async def process_and_respond(phone_number: str, message_body: str):
    """Procesa el mensaje con ALY y responde activamente via Twilio."""
    whatsapp_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
    to_number = f"whatsapp:{phone_number}"

    try:
        if not orchestrator:
            twilio_client.messages.create(
                body="Sistema no disponible temporalmente. Intenta más tarde.",
                from_=whatsapp_number,
                to=to_number
            )
            return

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(executor, orchestrator.process_query, message_body)

        response_text = result.get('answer', 'No pude procesar tu consulta. Intenta de nuevo.')
        intent = result.get('intent', 'FACTUAL')
        language = result.get('language_detected', 'es')

        # Enviar respuesta principal (dividida si es larga)
        await send_whatsapp(to_number, whatsapp_number, response_text)
        logger.info(f"✅ Respuesta enviada a {phone_number} (intent: {intent}, lang: {language})")

        # Follow-up después de la primera respuesta real (no greeting)
        if intent != 'GREETING':
            from config.welcome_messages import get_follow_up_messages
            follow_up = get_follow_up_messages(language)
            twilio_client.messages.create(body=follow_up['message_1'], from_=whatsapp_number, to=to_number)
            twilio_client.messages.create(body=follow_up['message_2'], from_=whatsapp_number, to=to_number)
            logger.info(f"✅ Follow-up enviado ({language})")

    except Exception as e:
        logger.error(f"❌ Error procesando mensaje: {e}")
        try:
            twilio_client.messages.create(
                body="Disculpa, tuve un problema técnico. ¿Puedes intentar de nuevo?",
                from_=whatsapp_number,
                to=to_number
            )
        except Exception:
            pass


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None)
):
    """Webhook principal - responde inmediatamente a Twilio, procesa en background."""
    phone_number = From.replace('whatsapp:', '')
    message_body = Body.strip()

    logger.info(f"📱 Mensaje de {phone_number}: {message_body[:80]}")

    asyncio.create_task(process_and_respond(phone_number, message_body))

    return PlainTextResponse("", media_type="text/plain")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "bot": "Aly Apapachar",
        "document": "Manual A+P (ICBF)",
        "timestamp": datetime.now().isoformat(),
        "orchestrator": "ready" if orchestrator else "initializing",
        "twilio": "ready" if twilio_client else "not_ready"
    }


if __name__ == "__main__":
    logger.info("🚀 Iniciando Aly Apapachar WhatsApp Bot...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003, reload=False, log_level="info")
