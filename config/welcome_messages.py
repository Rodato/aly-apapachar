#!/usr/bin/env python3
"""
Welcome Messages - Aly Apapachar
Mensajes del programa A+P (Apapáchar) en 3 idiomas
"""

WELCOME_MESSAGES = {
    'es': """¡Hola! Soy Aly, tu asistente para el programa Apapáchar (A+P).

Estoy aquí para ayudarte a entender e implementar el Manual A+P del ICBF. Puedes preguntarme sobre actividades, metodología, objetivos del programa, cómo facilitar sesiones, y más.

¿En qué te puedo ayudar hoy?""",

    'en': """Hello! I'm Aly, your assistant for the Apapáchar (A+P) program.

I'm here to help you understand and implement the A+P Manual (ICBF). You can ask me about activities, methodology, program goals, how to facilitate sessions, and more.

How can I help you today?""",

    'pt': """Olá! Sou Aly, sua assistente para o programa Apapáchar (A+P).

Estou aqui para ajudá-lo a entender e implementar o Manual A+P do ICBF. Você pode me perguntar sobre atividades, metodologia, objetivos do programa, como facilitar sessões e muito mais.

Como posso ajudá-lo hoje?"""
}

SENSITIVE_MESSAGES = {
    'es': """Entiendo que este es un tema delicado. Mi función es apoyarte con el contenido del programa A+P.

Para situaciones que requieren apoyo emocional o intervención especializada, por favor contacta a los recursos de apoyo de tu institución o al equipo de Equimundo.

¿Hay algo específico del Manual A+P en lo que pueda ayudarte?""",

    'en': """I understand this is a sensitive topic. My role is to support you with the A+P program content.

For situations requiring emotional support or specialized intervention, please contact your institution's support resources or the Equimundo team.

Is there something specific in the A+P Manual I can help you with?""",

    'pt': """Entendo que este é um tópico delicado. Minha função é apoiá-lo com o conteúdo do programa A+P.

Para situações que requerem apoio emocional ou intervenção especializada, entre em contato com os recursos de apoio da sua instituição ou com a equipe da Equimundo.

Há algo específico no Manual A+P com que eu possa ajudá-lo?"""
}

FOLLOW_UP_MESSAGES = {
    'es': {
        'message_1': "¿Te fue útil esta información? ¿Tienes alguna otra pregunta sobre el programa A+P?",
        'message_2': "Recuerda que puedo ayudarte con cualquier parte del Manual A+P: actividades, objetivos, metodología o cómo adaptar el programa."
    },
    'en': {
        'message_1': "Was this information helpful? Do you have any other questions about the A+P program?",
        'message_2': "Remember, I can help you with any part of the A+P Manual: activities, objectives, methodology, or how to adapt the program."
    },
    'pt': {
        'message_1': "Essa informação foi útil? Você tem alguma outra pergunta sobre o programa A+P?",
        'message_2': "Lembre-se que posso ajudá-lo com qualquer parte do Manual A+P: atividades, objetivos, metodologia ou como adaptar o programa."
    }
}


def get_welcome_message(language_code: str) -> str:
    return WELCOME_MESSAGES.get(language_code, WELCOME_MESSAGES['es'])


def get_sensitive_message(language_code: str) -> str:
    return SENSITIVE_MESSAGES.get(language_code, SENSITIVE_MESSAGES['es'])


def get_follow_up_messages(language_code: str) -> dict:
    return FOLLOW_UP_MESSAGES.get(language_code, FOLLOW_UP_MESSAGES['es'])
