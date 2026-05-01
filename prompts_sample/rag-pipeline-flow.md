# RAG Pipeline Flow: Brainstorm & Workshop Routes

This document explains step-by-step how a user question flows through the multi-agent RAG pipeline when using the **Brainstorm** or **Workshop** endpoints.

---

## Entry Points

| Route | File | Mode |
|-------|------|------|
| `POST /api/rag/doQuestion/brainstorm` | `src/router/rag/connection/doQuestion/brainstorm/post.ts` | Brainstorm |
| `POST /api/rag/doQuestion/workshop` | `src/router/rag/connection/doQuestion/workshop/post.ts` | Workshop |

Both routes receive the same payload:
```json
{
  "userQuestion": "How can I introduce respect in a session?",
  "userNumber": "+5511999999999"
}
```

---

## Step-by-Step Pipeline

### Step 1 — Route Handler receives the request

The route handler (`brainstorm/post.ts` or `workshop/post.ts`):

1. Validates the body using Elysia's Zod-like schema (`t.Object({ userQuestion, userNumber })`)
2. Lazy-initializes the `LangChainRAGService` singleton (connects to Qdrant on first call)
3. Loads the mode-specific prompt from `RAG_CONSTANTS`
4. Calls `ragService.processQuestion(userQuestion, AGENT_PROMPT, userNumber)`

**The key difference between routes is which prompt gets loaded:**

#### Brainstorm Prompt (`RAG_CONSTANTS.BRAINSTORM_AGENT_PROMPT`)
```
You are a creative facilitator guide. Offer 3-5 inclusive and safe activity ideas based on the
user's topic or goal. Your job is to spark options, not provide a final answer.

## Structure:
**Topic:** <summary>
Here are some ideas to explore:
**1- [Title]**: [->line summary]
-> **Try:** [short example or phrasing]
**2- [Title]**: [->line summary]…
Prompt for action: "Want help adapting one of these?"

## Tone:
- Curious, supportive, and flexible
- Never judgmental or moralizing
- Don't use academic terms like "intervention" or "learning objective"

## Edge Handling:
- If gender/religion/etc.: "Let's try a version that leaves space for different perspectives."
- If vague input: "Here are a few ways this could go — which one fits your setting?"

## SAFE_EDGE_HANDLER (Sensitive Topic Redirect)
When user asks about topics that go beyond classroom practice (e.g., trauma, religion, discipline
at home), reroute with affirming redirection:
- "That's a really important issue. While I can't guide you directly on that, here's one way to
  support students safely through your sessions."
- Then offer a related classroom activity, reflection, or strategy.

## FALLBACK PROMPT (Unclear Input)
If the input is unclear:
- "Just to be sure — are you looking to:
  1) Explore ideas? or
  2) Adapt something you're already using?"

If still unclear, suggest:
- "Would you like to see a few activities others have used for this topic?"

## FEW-SHOT RESPONSE ANCHORS (HIDDEN)
• Workshop Agent Example: Q: "How do I adapt the Strength Shield activity for students who can't
  write yet?" → Topic: Strength Shield — low-literacy version Plan:
  Draw shield outlines on the board
  Ask students what makes them feel strong
  Let them point, gesture, or use images Tips:
  Accept all forms of expression Sample Phrase: "Show me with your body — what strength looks
  like." Reminder: You're making strengths visible without needing words.

• Brainstorming Agent Example: Q: "How can I introduce respect in a session?" → Topic: Respect —
  session openers Ideas:
  Respect Wall — Students post ways to show respect Try: "Add one idea to our wall of respect."
  Mirror Game — Pair up and mirror each other silently Try: "Take turns being the leader — notice
  what feels respectful."
  Role Card Swap — Students draw role cards (teacher, parent, peer) and act with respect Try:
  "How would you show respect in this role?"

## TONE ENFORCEMENT
Always warm, simple, inclusive
Validate teacher agency: "You know your group — adapt as needed."
No prescriptive tone ("You must…")
No moralizing or "correct" framing
```

- **Extra behavior**: None. Returns response directly to client.

#### Workshop Prompt (`RAG_CONSTANTS.WORKSHOP_AGENT_PROMPT`)
```
You are a planning assistant for educators. Help the user turn a known activity, challenge, or
lesson into a small, clear, realistic plan they can apply in their next session.

## Structure your response as:
**Topic:** <summary>
**Suggested Plan:**
1-> **[Step Name]:** ...
2-> **[Step Name]:** ...

**Tips:**
-> ...

**Sample Phrase:** "..."

**FORMATTING RULES:**

- Numbered lists MUST Use bold format like: "**1- Title:**".
- Sub-items must use bold format with "-> ".

Reminder: You can adjust this based on your students' needs.

## Safety Layer:
- If user appears overwhelmed, begin with: "Let's break this into one small thing you could try."
- If the topic touches gender/identity, use: "This can be sensitive — here's one way to invite
  reflection without forcing disclosure."

## Constraints:
- Never invent strategies. Only adapt what's already known.
- Do not give advice on family, therapy, or identity.
```

- **Extra behavior**: Workshop saves every response to a JSON file in `/responses/response<timestamp>.json`

---

### Step 2 — Agent 0: Question Contextualization

**Method:** `_contextualizeQuestion(question, chatHistory)`
**Model:** `openai/gpt-4o-mini` via OpenRouter
**Temperature:** 0.1 | **Max tokens:** 150

**What it does:**
- Retrieves the last 3 conversation interactions for this `userNumber` from MongoDB
- If there is NO history → skips this step, returns the original question unchanged
- If there IS history → sends the question + history to the LLM with this prompt:

```
Given the conversation history and a NEW user question, rephrase the question to be standalone
ONLY IF it depends on history context.

RULES:
1. If the question refers to entities from history (e.g., "it", "that", "the previous one"),
   replace them with specific terms.
2. If the question is a direct follow-up (e.g., "tell me more", "why?"), combine it with
   previous context.
3. If the question is UNRELATED to history or changes topic, return it EXACTLY as provided.
4. Do NOT answer the question - only rephrase it.

#######################################################
# CRITICAL LANGUAGE RULE
#######################################################
The output MUST be in the EXACT SAME LANGUAGE as the "New User Question".
- If New User Question is in English → Output MUST be in English
- If New User Question is in Portuguese → Output MUST be in Portuguese
- If New User Question is in Spanish → Output MUST be in Spanish

IGNORE the language of the History section completely.
ONLY match the language of the New User Question.
#######################################################

History:
<< chat history messages formatted as "role: content" >>

New User Question: << the user's question >>

Rephrased Question (SAME LANGUAGE as New User Question):
```

**Example:**
- History: User asked about "Boys Club program"
- New question: "Tell me more about it"
- Output: "Tell me more about the Boys Club program"

---

### Step 3 — Agent 1: Keyword Extraction

**Method:** `_extractQuestionKeywords(contextualizedQuestion)`
**Model:** `openai/gpt-4o-mini` via OpenRouter
**Temperature:** 0.1 | **Max tokens:** 100

**What it does:**
- Takes the contextualized question and extracts 3-5 search keywords
- **CRITICAL:** Keywords are ALWAYS extracted in English, regardless of the user's language (because Qdrant metadata is indexed in English)

**Complete prompt:**

```
Extract 3-5 keywords and phrases from this question.

CRITICAL RULES:
1. Focus on technical terms, entities, and compound concepts (e.g., "many ways of being",
   "early childhood development", "mwb").
2. Keep compound terms together.
3. **IMPORTANT**: ALL keywords MUST be in ENGLISH, regardless of the question's language.
   - If the question is in Portuguese, translate the keywords to English.
   - If the question is in Spanish, translate the keywords to English.
   - Proper nouns (names of programs, people, places) should be kept as-is.
4. Return ONLY a JSON array of strings in lowercase.

Examples:
- Question (PT): "Quais são os benefícios do programa Boys Club?"
  Keywords: ["benefits", "boys club", "program"]

- Question (ES): "¿Cómo implementar actividades de masculinidades?"
  Keywords: ["masculinities", "activities", "implementation"]

- Question (EN): "What is the Apapachar program about?"
  Keywords: ["apapachar", "program"]

Question: << the contextualized question >>

Keywords in ENGLISH (only JSON):
```

**Output:** `["respect", "session", "activities", "introduction"]`

**Fallback:** If JSON parsing fails, uses regex to extract quoted strings. If still empty, returns `[]`.

---

### Step 4 — Agent 2: Document Identification (Pre-filtering)

**Method:** `qdrantService.getDocumentIdsByKeywords(keywords)`
**No LLM call** — this is a direct Qdrant metadata filter query.

**What it does:**
- Takes the English keywords from Agent 1
- Queries Qdrant's `alybot` collection to find documents whose `keywords` payload field matches any of the extracted keywords
- Returns a list of `documentId` strings that are relevant to the question

**Purpose:** Narrows down the search space so Agent 3 can do a more focused embedding search on specific documents, rather than searching the entire collection.

**Example output:** `["doc-uuid-1", "doc-uuid-3"]` (documents about "respect" and "sessions")

---

### Step 5 — Agent 3: Hybrid Embedding Search (runs 2 searches in parallel)

**Method:** `_embeddingSearchAgent(contextualizedQuestion, filterDocumentIds?)`
**Embedding model:** `openai/text-embedding-3-large` (3072 dimensions)
**Distance metric:** Cosine similarity
**Top-K:** 5 results per search

Two parallel searches are launched simultaneously:

#### Search A — Global Search (no document filter)
- Generates an embedding vector from the contextualized question
- Searches ALL vectors in the `alybot` Qdrant collection
- Returns top 5 most similar chunks with scores

#### Search B — Targeted Search (filtered by Agent 2's document IDs)
- Same embedding vector
- Only searches within the documents identified by Agent 2
- Returns top 5 most similar chunks from those specific documents
- **Skipped** if Agent 2 found no matching documents

Both searches run via `Promise.all()` for performance.

**Output per search:**
```json
[
  {
    "documentId": "uuid-123",
    "documentName": "Boys_Club_Manual.md",
    "text": "The respect activity involves...",
    "score": 0.87
  }
]
```

---

### Step 6 — Agent 4: Orchestrator (Response Generation)

**Method:** `_orchestratorAgent(...)`
**Model:** `openai/gpt-4o-mini` via OpenRouter
**Temperature:** 0.7 | **Max tokens:** 1500

This is the main agent that generates the final answer. It performs several sub-steps:

#### 6a — Deduplicate chunks
- Merges results from Global Search and Targeted Search
- Uses `documentId + first 20 chars of text` as a deduplication key
- If a chunk appears in both searches, marks it as `matchType: "both"` and keeps the higher score
- Sorts all unique chunks by score (highest first)

#### 6b — Detect user language

**Sub-call:** `_detectLanguageWithLLM(originalUserQuestion)`
- Sends the **original** user question (NOT the contextualized one) to the LLM
- Temperature: 0 | Max tokens: 10
- Returns: `"PORTUGUESE"`, `"SPANISH"`, or `"ENGLISH"`

**Complete prompt:**

```
Identify the language of this text. Reply with ONLY one word: PORTUGUESE, SPANISH, or ENGLISH.

Text: "<< the original user question >>"

Language:
```

#### 6c — Retrieve chat history
- Fetches last 3 interactions from MongoDB for this `userNumber`
- Formats them as `Turn N: User: ... / Assistant: ...`

#### 6d — Build the final system prompt

Calls `RAG_CONSTANTS.systemPrompt(agentPrompt, question, documentContext, chatHistory, targetLanguage)` which assembles the following complete prompt (example with PORTUGUESE as detected language):

```
#######################################################
# RESPONSE LANGUAGE: PORTUGUESE
# YOUR ENTIRE RESPONSE MUST BE IN PORTUGUESE.
# THIS IS MANDATORY AND NON-NEGOTIABLE.
#######################################################

You are Aly, a friendly assistant from Equimundo.
You help educators apply and adapt programs like Boys Club, Lifting Barriers, and Apapachar.

## FORMATTING (USE MARKDOWN)
- **bold** for titles and important points
- *italic* for emphasis
- -> for bullet lists
- 1- for numbered lists
- NEVER use backslash (\) at the end of a line for line breaks. Just use normal line breaks.

## TONE
- Warm, friendly, conversational
- Use emojis sparingly (😊✨💬)
- Validate the teacher's role
- Keep responses concise and practical

## AGENT INSTRUCTIONS
<< THE COMPLETE BRAINSTORM OR WORKSHOP PROMPT FROM STEP 1 IS INSERTED HERE >>

## CHAT HISTORY (context only)
Turn 1:
User: << previous question >>
Assistant: << previous answer >>

Turn 2:
User: << previous question >>
Assistant: << previous answer >>

Turn 3:
User: << previous question >>
Assistant: << previous answer >>

## USER MESSAGE
<< The contextualized question from Agent 0 >>

## REFERENCE DOCUMENTS
<< chunk 1 text >>

---

<< chunk 2 text >>

---

<< chunk N text >>

## FOOTER (add at the end after 2 line breaks)
conversando com o modo **Workshop**, digite 'Brainstorm' para mudar ou 'menu' para selecionar
outro modo.

#######################################################
# REMINDER: RESPOND ENTIRELY IN PORTUGUESE
#######################################################
```

**Footer variations by language:**

| Language | Footer text |
| --- | --- |
| ENGLISH | chatting with **Workshop** mode, type 'Brainstorm' to change or 'menu' to select another mode. |
| SPANISH | chateando con el modo **Workshop**, escribe 'Brainstorm' para cambiar o 'menú' para seleccionar otro modo. |
| PORTUGUESE | conversando com o modo **Workshop**, digite 'Brainstorm' para mudar ou 'menu' para selecionar outro modo. |

#### 6e — Call the LLM
- Sends the assembled prompt to `openai/gpt-4o-mini`
- Gets the generated answer

---

### Step 7 — Agent 5: Translation Verification

**Method:** `_translationAgent(answer, targetLanguage)`
**Model:** `openai/gpt-4o-mini` via OpenRouter
**Temperature:** 0 | **Max tokens:** 3000

**What it does:**
- Takes the answer from Agent 4 and the detected target language
- Acts as a **final safety gate** to ensure the response is in the correct language
- Translates the entire response (including footer) to the target language

**Complete prompt** (example with PORTUGUESE as target language):

```
You are a translator. Translate the following text to PORTUGUESE.

TEXT TO TRANSLATE:
<< the answer generated by Agent 4 >>

RULES:
1. Translate the ENTIRE text to PORTUGUESE.
2. Preserve all markdown formatting (**, ->, emojis).
3. Translate the footer message too.
4. Do NOT wrap output in quotes.
5. Do NOT add explanations or comments.
6. Output ONLY the translated text.
7. NEVER use backslash (\) at the end of a line for line breaks. Use normal line breaks only.

TRANSLATED TEXT IN PORTUGUESE:
```

**Post-processing:**

- Strips wrapping quotes (single or double) if the model adds them
- Strips escaped quotes (`\"`) at start/end

**Fallback:** If translation returns a response shorter than 50 characters, keeps the original answer from Agent 4 unchanged.

---

### Step 8 — Post-processing & Persistence (background, non-blocking)

After Agent 5 returns the final answer:

#### 8a — Clean up formatting
- Removes all `###` markdown headers (not supported in WhatsApp)
- Removes trailing spaces, tabs, and backslashes before newlines (iPhone renders these as literal characters)

#### 8b — Save to MongoDB (async, fire-and-forget)
Saves to the `RagHistory` collection:
```json
{
  "userNumber": "+5511999999999",
  "interactions": [{
    "userQuestion": "How can I introduce respect in a session?",
    "assistantAnswer": "<<final translated answer>>",
    "chunks": [{ "documentName": "...", "documentId": "...", "score": 0.87 }],
    "timestamp": "2026-03-16T..."
  }]
}
```

#### 8c — Save to SQLite (async, fire-and-forget)
Backup log in `conversationsLog.db` for audit trail / data loss prevention.

#### 8d — Workshop-only: Save response to JSON file
Workshop route additionally writes the full response to `/responses/response<timestamp>.json`.

---

### Step 9 — Return Response

The route handler returns the result to the client:

```json
{
  "success": true,
  "question": "How can I introduce respect in a session?",
  "answer": "<<final translated and cleaned answer>>"
}
```

The full `QueryResponse` object (used internally) also includes:
```json
{
  "sources": [
    { "documentId": "uuid", "documentName": "Manual.md", "score": 0.87, "matchType": "both" }
  ],
  "chunks": [ ... ],
  "metadata": {
    "keywordMatchCount": 5,
    "embeddingMatchCount": 5,
    "totalTokens": 1234
  }
}
```

---

## Visual Summary

```
User Question
    │
    ▼
┌─────────────────────────────────────────────┐
│  Route Handler (brainstorm/ or workshop/)    │
│  Loads mode-specific prompt from RAG_CONSTANTS│
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  Agent 0: Contextualize Question            │
│  LLM rephrases using chat history           │
│  (skipped if no history)                    │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  Agent 1: Keyword Extraction                │
│  LLM extracts 3-5 English keywords         │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  Agent 2: Document Identification           │
│  Qdrant metadata filter by keywords         │
│  Returns matching document IDs              │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  Agent 3: Hybrid Embedding Search           │
│  ┌──────────────┐  ┌────────────────────┐   │
│  │ Global Search │  │ Targeted Search    │   │
│  │ (all docs)   │  │ (Agent 2 doc IDs)  │   │
│  └──────┬───────┘  └────────┬───────────┘   │
│         └────────┬──────────┘               │
│                  ▼                           │
│         Top 5 + Top 5 chunks                │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  Agent 4: Orchestrator                      │
│  1. Deduplicates chunks                     │
│  2. Detects user language (LLM)             │
│  3. Retrieves chat history (MongoDB)        │
│  4. Builds system prompt with:              │
│     - Mode prompt (Brainstorm/Workshop)     │
│     - Document chunks as context            │
│     - Chat history                          │
│     - Language instructions                 │
│  5. Generates answer (LLM)                  │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  Agent 5: Translation Verification          │
│  LLM translates to detected language        │
│  (safety gate for correct language output)  │
└─────────────┬───────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────┐
│  Post-processing                            │
│  - Strip ### headers                        │
│  - Clean trailing whitespace/backslashes    │
│  - Save to MongoDB (async)                  │
│  - Save to SQLite (async)                   │
│  - [Workshop only] Save JSON file           │
└─────────────┬───────────────────────────────┘
              │
              ▼
         Return Response
```

---

## LLM Calls Summary

| Step | Agent | Model | Temperature | Purpose |
|------|-------|-------|-------------|---------|
| 2 | Agent 0 | gpt-4o-mini | 0.1 | Rephrase question with history context |
| 3 | Agent 1 | gpt-4o-mini | 0.1 | Extract English keywords |
| 5 | Agent 3 | text-embedding-3-large | — | Generate query embedding vector |
| 6b | (sub) | gpt-4o-mini | 0 | Detect user language |
| 6e | Agent 4 | gpt-4o-mini | 0.7 | Generate final answer |
| 7 | Agent 5 | gpt-4o-mini | 0 | Translate to user language |

**Total LLM calls per question: 5** (+ 1 embedding generation)
