# AI Personal Assistant Agent

A starter personal assistant agent for this repository, designed for practical day-to-day task and note management.

## Features

- Provider-agnostic LLM runtime: **OpenAI**, **Anthropic**, **Google**, or **NVIDIA NIM**
- **Extensible capabilities**: add new tools without changing core agent logic
- Built-in: task management, notes, daily planner
- Optional: **web search** (ddgs metasearch, no API key) — enable with `ENABLE_WEB_SEARCH=1`
- Optional: **controller / code evolution** — when the agent cannot do something, it can add new capabilities via web search + code generation. Enable with `ENABLE_CODE_EVOLUTION=1` (requires `ENABLE_WEB_SEARCH=1`)
- Optional startup model refresh from provider docs pages

## Why this project exists

This app is the **#1 requested agent type** from the keyword research step: AI personal assistant.

## Project structure

```text
ai_personal_assistant_agent/
├── app/
│   ├── capabilities/          # Extensible tool registry
│   │   ├── __init__.py       # Registry + get_all_tools()
│   │   ├── tasks_notes.py    # Task/note tools (always on)
│   │   ├── web_search.py     # Web search (opt-in)
│   │   └── code_evolution.py # Controller: add capabilities when agent cannot do something (opt-in)
│   ├── agent.py
│   ├── config.py
│   ├── model_factory.py
│   ├── model_recommender.py
│   ├── storage.py
│   └── tools.py
├── .env.example
├── main.py
└── requirements.txt
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy and configure env file:

```bash
cp .env.example .env
```

4. Set `LLM_PROVIDER` and the corresponding API key in `.env`:
   - **OpenAI**: `OPENAI_API_KEY`
   - **Anthropic**: `ANTHROPIC_API_KEY`
   - **Google**: `GOOGLE_API_KEY`
   - **NVIDIA NIM**: `NIM_API_KEY` (or `NVIDIA_API_KEY`)

## Run

```bash
python main.py
```

---

## Deploy to Vercel

1. **Connect GitHub** to Vercel and import the repo.
2. **Set Root Directory** in project settings to `starter_ai_agents/ai_personal_assistant_agent`.
3. **Add environment variables** in Vercel:
   - `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `NIM_API_KEY` for other providers)
   - `LLM_PROVIDER` (default: `openai`)
   - `ENABLE_WEB_SEARCH=1` (optional)
   - `ASSISTANT_DATA_FILE=/tmp/assistant_state.json` (optional; default for serverless)
4. **Deploy**. The chat UI is at `/index.html`, API at `POST /api/chat`.

**API usage:**
```bash
curl -X POST https://your-app.vercel.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Add a task: buy milk", "chat_history": []}'
```

**Note:** Code evolution (`ENABLE_CODE_EVOLUTION`) is disabled on Vercel (read-only filesystem). Tasks/notes use ephemeral storage (`/tmp`) unless you add Vercel KV or a database.

---

## Provider options and model recommendations

You can use either **cloud providers** (OpenAI, Anthropic, Google) or **NVIDIA NIM** (hosted or self-hosted). Set `LLM_PROVIDER` in `.env` and optionally `MODEL_NAME` to pick a specific model.

### Cloud providers (OpenAI, Anthropic, Google)

| Provider   | Best for                    | Recommended models (set `MODEL_NAME`) |
|-----------|-----------------------------|----------------------------------------|
| **OpenAI** | Production, coding agents   | `gpt-5.2`, `gpt-5-mini`, `gpt-4o`      |
| **Anthropic** | Long context, reasoning | `claude-opus-4-6`, `claude-sonnet-4-5` |
| **Google** | Multimodal, cost-efficient | `gemini-2.5-pro`, `gemini-2.5-flash`    |

**Defaults** (when `MODEL_NAME` is unset and web refresh is enabled):  
OpenAI `gpt-5-mini`, Anthropic `claude-sonnet-4-5`, Google `gemini-2.5-pro`.

### NVIDIA NIM (hosted or self-hosted)

NVIDIA NIM offers OpenAI-compatible APIs. Use it when you want:

- **Self-hosted** or **on-prem** deployment
- **Open-weight** models (Llama, Nemotron, Qwen, Mistral)
- **No vendor lock-in** to cloud LLM APIs

**Environment variables for NVIDIA:**

| Variable      | Description |
|---------------|-------------|
| `NIM_API_KEY` | API key from [build.nvidia.com](https://build.nvidia.com) (hosted) or your deployment |
| `NIM_BASE_URL` | Base URL. Default: `https://integrate.api.nvidia.com/v1` for hosted NIM. For self-hosted, use your endpoint (e.g. `http://localhost:8000/v1`). |

**Recommended NVIDIA NIM models** (all support tool calling):

| Use case              | Model name |
|-----------------------|------------|
| **Best quality**      | `nvidia/llama-3.3-nemotron-super-49b-v1.5` |
| **Strong reasoning** | `openai/gpt-oss-120b` |
| **Balanced**          | `qwen/qwen3-next-80b-a3b-instruct`, `meta/llama-3.1-70b-instruct` |
| **Fast / lightweight** | `meta/llama-3.1-8b-instruct`, `nvidia/llama-3.1-nemotron-nano-8b-v1` |
| **Very small**        | `mistralai/mistral-7b-instruct-v0.3` |

**Example `.env` for NVIDIA (hosted):**

```bash
LLM_PROVIDER=nvidia
NIM_API_KEY=your-nvidia-api-key
MODEL_NAME=meta/llama-3.1-8b-instruct
```

**Example `.env` for NVIDIA (self-hosted NIM):**

```bash
LLM_PROVIDER=nvidia
NIM_API_KEY=not-used
NIM_BASE_URL=http://localhost:8000/v1
MODEL_NAME=nvidia/llama-3.1-nemotron-nano-8b-v1
```

---

## Model selection behavior

At startup, the app chooses a model in this order:

1. **`MODEL_NAME`** from `.env` (explicit override) — use this to pin a specific model.
2. If **`ENABLE_MODEL_WEB_REFRESH=true`**, it fetches provider docs and tries to infer a suitable model (cloud providers only; NVIDIA uses curated defaults).
3. **Fallback defaults**:
   - OpenAI: `gpt-5-mini`
   - Anthropic: `claude-sonnet-4-5`
   - Google: `gemini-2.5-pro`
   - NVIDIA: `meta/llama-3.1-8b-instruct`

---

## Controller and code evolution

When `ENABLE_CODE_EVOLUTION=1` (and `ENABLE_WEB_SEARCH=1`), the agent runs in **controller mode**:

1. **Controller agent** sits above capability agents. When a request cannot be fulfilled with current tools, it:
   - Uses `web_search` to find how to implement the missing capability (e.g. "python fetch emails imap")
   - Uses `add_capability` to write a new capability module and install dependencies
   - The agent is rebuilt with the new tools; the user can ask again

2. **Flow**: User asks → agent tries → if it cannot, it searches the web → generates code → adds capability → agent rebuilds → user asks again

3. **Safety**: Only writes to `app/capabilities/*.py`. Requires explicit opt-in via env.

```bash
ENABLE_WEB_SEARCH=1
ENABLE_CODE_EVOLUTION=1
```

---

## Adding new capabilities (manual)

The agent uses a **capability registry**: each capability is a module that registers tools. To add a new capability (e.g. email, database, APIs):

1. **Create** `app/capabilities/your_capability.py`:

```python
from langchain_core.tools import tool
from app.capabilities import register_capability

def _get_tools(**kwargs):
    @tool
    def your_tool(arg: str) -> str:
        """Description for the LLM."""
        return "result"

    return [your_tool]

# None = always on; "ENABLE_X" = on only when env is set
register_capability("your_capability", _get_tools, enable_env_var="ENABLE_YOUR_CAPABILITY")
```

2. **Import** it in `app/capabilities/__init__.py`:

```python
from app.capabilities import your_capability  # noqa: F401, E402
```

3. **Enable** via `.env` if you used `enable_env_var`:

```bash
ENABLE_YOUR_CAPABILITY=1
```

The agent will automatically pick up the new tools. No changes to `agent.py` or `main.py` are needed.

---

## Notes

- No API keys are hardcoded.
- Persistent memory is local JSON (`assistant_state.json`).
- This is an educational starter; add auth, encryption, and stronger validation for production use.
