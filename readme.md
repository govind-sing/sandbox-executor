markdown
# Sandbox Executor

A natural language to artifact generator. You describe what you want — a chart, audio file, PDF, data table — and the system uses an LLM to write Python code, executes it inside an isolated Docker sandbox, and returns the result rendered in the browser.

## How it works

User Prompt → Gemini LLM → Generated Python Code → Docker Sandbox → Rendered Output


1. User submits a prompt (and optional context) from the frontend
2. Backend sends the prompt to Gemini, which returns structured JSON containing Python code and output metadata
3. Backend spins up an ephemeral Docker container, runs the code inside it, and reads the output file
4. The output is base64 encoded and returned to the frontend
5. Frontend renders the result based on output type — image, audio, PDF, CSV table, or text
6. The sandbox container is destroyed immediately after execution

## Supported output types

| Ask for | Example prompt | Returns |
|---|---|---|
| Chart / graph | "Give me a bar chart of top 5 programming languages by popularity" | PNG image |
| Audio | "Create an audio jingle for a coffee shop" | MP3 player |
| PDF | "Generate a PDF report on climate change summary" | Downloadable PDF |
| Table | "Give me a CSV of G20 countries with GDP and population" | Rendered table |
| Text | "Write a poem about the ocean" | Text output |

## Tech stack

**Backend**
- FastAPI — REST API
- Google Gemini (`gemini-2.0-flash`) — code generation
- Docker SDK for Python — sandbox orchestration
- Python 3.11

**Frontend**
- React 18 + Vite
- Tailwind CSS

**Sandbox**
- Ephemeral Docker containers (one per request, destroyed after)
- Resource limits: 256MB RAM, 50% CPU, no network access
- Pre-installed: `matplotlib`, `pandas`, `numpy`, `pydub`, `reportlab`, `Pillow`, `scipy`, `seaborn`

## Project structure

sandbox-executor/
├── sandbox/
│ └── Dockerfile # sandbox image for code execution
├── frontend/
│ ├── Dockerfile
│ ├── index.html
│ ├── vite.config.js
│ ├── tailwind.config.js
│ ├── postcss.config.js
│ ├── package.json
│ └── src/
│ ├── main.jsx
│ ├── index.css
│ └── App.jsx
├── main.py # FastAPI app
├── executor.py # Docker sandbox execution
├── llm.py # Gemini integration
├── requirements.txt
├── Dockerfile # backend image
└── docker-compose.yml


## Prerequisites

- Docker and Docker Compose installed and running
- A Gemini API key — get one at [aistudio.google.com](https://aistudio.google.com)

## Setup

**1. Clone the repo**

```bash
git clone https://github.com/your-username/sandbox-executor.git
cd sandbox-executor
```

**2. Create your `.env` file**

```bash
cp .env.example .env
```

Open `.env` and add your key:

GEMINI_API_KEY=your_key_here


**3. Build the sandbox image**

This is a one-time step. The sandbox image is the isolated Python environment every code execution runs inside.

```bash
docker build -t sandbox-executor ./sandbox
```

**4. Start everything**

```bash
docker compose up --build
```

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend: [http://localhost:8000](http://localhost:8000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## API

### `POST /execute`

Accepts a prompt, generates code, executes it, returns the result.

**Request**
```json
{
  "prompt": "Give me a pie chart of population by continent",
  "context": ""
}
```

**Response (success)**
```json
{
  "success": true,
  "output_type": "image",
  "description": "Pie chart showing population distribution by continent",
  "data": "<base64 encoded file>",
  "code": "import matplotlib..."
}
```

**Response (failure)**
```json
{
  "success": false,
  "error": "Expected output file 'output.png' was not created.",
  "code": "import matplotlib..."
}
```

### `GET /health`

```json
{ "status": "ok" }
```

## Security model

Each code execution runs in a fresh Docker container with:

- **No network access** — `network_disabled: true`, containers cannot make external requests
- **Memory cap** — 256MB limit per container
- **CPU cap** — 50% of one core per container
- **Filesystem isolation** — only the `/sandbox` working directory is mounted, nothing else on the host is accessible
- **Auto cleanup** — containers are force-removed immediately after execution regardless of success or failure
- **No persistence** — each container starts clean with no state from previous executions

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Your Google Gemini API key |

## Add a `.env.example` to your repo

GEMINI_API_KEY=your_gemini_api_key_here


## Add a `.gitignore`

Make sure your `.env` is never committed:

.env
pycache/
*.pyc
node_modules/
frontend/node_modules/
dist/


## Local development (without Docker)

If you want to run the backend locally without Docker for faster iteration:

```bash
# backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Note: You still need Docker running on your machine for the sandbox containers even in local dev mode.

## Known limitations

- Sandbox containers can only use the pre-installed Python libraries. If generated code tries to import something not in the sandbox image, execution will fail.
- Audio generation is limited — `pydub` can manipulate audio but cannot synthesize it from scratch. Prompts asking for sung audio or text-to-speech will not work without adding a TTS library to the sandbox image.
- Execution timeout is 30 seconds. Long-running code will be killed.
- No streaming — the UI shows a loading spinner until the full result is ready.

## Roadmap

- [ ] Streaming code generation so users see the LLM output in real time
- [ ] Execution history — save and revisit past results
- [ ] Add more sandbox libraries (TTS, image generation, networkx for graphs)
- [ ] File upload as context — let users upload a CSV and ask questions about it
- [ ] Multi-turn — refine the output with follow-up prompts

## License

MIT