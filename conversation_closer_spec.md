# Conversation Closer — Spec para Dev

## Prompt

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

4. "flag_reasoning": For EACH flag assigned, explain specifically WHY it was chosen. You MUST:
   - Quote or closely paraphrase the exact message or moment in the conversation that triggered the flag.
   - Explain what about that moment matches the flag definition.
   - If the flag is "general-inquiry", explain what makes the conversation routine and what concerning content is absent.
   Write in the SAME LANGUAGE as the transcript. Format as: "flag-name: [explanation]" for each flag, separated by newlines.

Respond ONLY with valid JSON, no other text. "flags" must always be a comma-separated string, never an array.

Transcript:
{transcription}
```

---

## Ejemplo de output esperado

```json
{
  "summary": "El facilitador solicitó ayuda para diseñar una sesión sobre rutinas familiares para niños de 10 años. Aly proporcionó un plan detallado con actividades adaptadas al grupo. La conversación terminó con el facilitador pidiendo opciones adicionales.",
  "keywords": "rutinas familiares, niños de 10 años, diseño de sesión, actividades participativas, convivencia familiar",
  "flags": "general-inquiry",
  "flag_reasoning": "general-inquiry: El facilitador hizo una solicitud rutinaria de diseño de sesión ('ayudame a diseñar una sesión de 60 min para hablar sobre rutinas familiares'). No hay contenido preocupante, divulgación personal, ni signos de angustia emocional."
}
```

---

## Columnas nuevas en Supabase — `conversations_data`

| Columna | Tipo | Origen | Descripción |
|---------|------|--------|-------------|
| `flag_reasoning` | `text` | LLM | Explicación de por qué se asignó cada flag, citando el momento concreto de la conversación. Viene en el JSON del LLM junto con summary, keywords y flags. |
| `flag_severity` | `text` | Backend | Severidad más alta presente en `flags`. Valores: `HIGH`, `MEDIUM`, `LOW`, `Operacional`. **No lo genera el LLM** — el backend lo calcula al guardar. |

### Lógica para calcular `flag_severity` (backend)

```python
def get_severity(flags_str: str) -> str:
    if "HIGH-" in flags_str:   return "HIGH"
    if "MEDIUM-" in flags_str: return "MEDIUM"
    if "LOW-" in flags_str:    return "LOW"
    return "Operacional"
```

---

## Modelo recomendado

`google/gemini-2.5-flash` vía OpenRouter — mejor razonamiento para detección de flags que gpt-4o-mini.
