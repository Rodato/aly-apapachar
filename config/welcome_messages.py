#!/usr/bin/env python3
"""
Welcome Messages - Aly Equimundo
Mensajes estáticos de bienvenida, sensitive y follow-up en 3 idiomas.
"""

WELCOME_MESSAGES = {
    'es': """¡Hola! Soy Aly, tu asistente de facilitación 🤖🌱

Estoy entrenada con la metodología de Equimundo y diseñada para apoyar a facilitadores como tú. Puedes preguntarme sobre actividades, cómo planear una sesión, adaptar materiales, resolver un desafío complejo u obtener ideas para involucrar a los participantes.

¡Lo que necesites! Solo pregúntame 😊""",

    'en': """Hello! I'm Aly, your facilitation assistant 🤖🌱

I'm trained on Equimundo's methodology and designed to support facilitators like you. You can ask me about activities, how to plan a session, adapt materials, tackle a complex challenge, or get ideas to engage participants.

Whatever you need — just ask! 😊""",

    'pt': """Olá! Sou Aly, sua assistente de facilitação 🤖🌱

Estou treinada com a metodologia da Equimundo e projetada para apoiar facilitadores como você. Pode me perguntar sobre atividades, como planejar uma sessão, adaptar materiais, resolver um desafio complexo ou obter ideias para engajar os participantes.

O que precisar — é só perguntar! 😊"""
}

SENSITIVE_MESSAGES = {
    'es': """Entiendo que estás tocando un tema muy importante y delicado.

Mi rol es apoyarte como facilitador/a en la implementación de los programas de Equimundo. Para situaciones que requieren atención especializada — apoyo emocional, intervención en crisis o acompañamiento clínico — lo más importante es conectar con los recursos adecuados de tu institución o con el equipo de Equimundo.

¿Hay algo relacionado con la facilitación de sesiones en lo que pueda ayudarte?""",

    'en': """I understand you're touching on a very important and sensitive topic.

My role is to support you as a facilitator in implementing Equimundo programs. For situations requiring specialized attention — emotional support, crisis intervention, or clinical care — the most important step is connecting with the right resources at your institution or with the Equimundo team.

Is there something related to session facilitation I can help you with?""",

    'pt': """Entendo que você está tocando em um tema muito importante e delicado.

Meu papel é apoiá-lo como facilitador/a na implementação dos programas da Equimundo. Para situações que requerem atenção especializada — apoio emocional, intervenção em crise ou acompanhamento clínico — o mais importante é conectar com os recursos adequados da sua instituição ou com a equipe da Equimundo.

Há algo relacionado à facilitação de sessões em que eu possa ajudá-lo?"""
}

FOLLOW_UP_MESSAGES = {
    'es': {
        'message_1': "¿Te fue útil esta información? ¿Tienes alguna otra pregunta?",
        'message_2': "Recuerda que puedo ayudarte a planear sesiones, adaptar actividades, resolver dudas sobre los programas de Equimundo o generar ideas creativas para tu grupo."
    },
    'en': {
        'message_1': "Was this information helpful? Do you have any other questions?",
        'message_2': "Remember, I can help you plan sessions, adapt activities, answer questions about Equimundo programs, or generate creative ideas for your group."
    },
    'pt': {
        'message_1': "Essa informação foi útil? Você tem alguma outra pergunta?",
        'message_2': "Lembre-se que posso ajudá-lo a planejar sessões, adaptar atividades, tirar dúvidas sobre os programas da Equimundo ou gerar ideias criativas para o seu grupo."
    }
}


def get_welcome_message(language_code: str) -> str:
    return WELCOME_MESSAGES.get(language_code, WELCOME_MESSAGES['es'])


def get_sensitive_message(language_code: str) -> str:
    return SENSITIVE_MESSAGES.get(language_code, SENSITIVE_MESSAGES['es'])


def get_follow_up_messages(language_code: str) -> dict:
    return FOLLOW_UP_MESSAGES.get(language_code, FOLLOW_UP_MESSAGES['es'])
