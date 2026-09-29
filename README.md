# Travel AI Assistant

A FastAPI-based multi-agent travel assistant that combines flight data, hotel search, itinerary generation, and PostgreSQL-backed conversation checkpoints.

## Features

- Flight search through AviationStack
- Hotel and web search through Tavily
- Travel itinerary generation with Groq
- Persistent LangGraph checkpoints in PostgreSQL
- FastAPI backend with a browser-based frontend
- Docker support

## Requirements

- Python 3.11+
- PostgreSQL
- API keys for Groq, Tavily, and AviationStack
- Docker Desktop (optional)

## Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
AVIATIONSTACK_API_KEY=your_aviationstack_api_key
DEFAULT_ORIGIN_IATA=DAC
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agent

# Optional LangSmith tracing
LANGSMITH_TRACING=false
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=TRAVEL
```

Do not commit `.env` or expose API keys. The included `.dockerignore` excludes `.env` from the Docker build context.

`DEFAULT_ORIGIN_IATA` must use this spelling. Older local configurations may contain the misspelled `DEFUALT_ORIGIN_IATA`, which the application does not read.

## Run Locally

From the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload
```

Open http://localhost:8000 in a browser.

## Run with Docker

Build the image:

```powershell
docker build -t travel-ai-assistant .
```

Run the application:

```powershell
docker run --rm --env-file .env -p 8000:8000 travel-ai-assistant
```

Open http://localhost:8000 in a browser.

When PostgreSQL is running on the Windows host, use this Docker-specific database URL:

```env
DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/agent
```

If PostgreSQL is running in another container, use that container or Compose service name as the database host instead.

## API

### `GET /`

Serves the web interface.

### `POST /chat`

Request body:

```json
{
  "message": "Plan a 5 day trip from Dhaka to Japan",
  "thread_id": "optional-conversation-id"
}
```

Example with PowerShell:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/chat `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message":"Plan a 5 day trip from Dhaka to Japan"}'
```

## Project Structure

```text
app.py                 FastAPI routes and static file serving
backend.py             LangGraph agents and PostgreSQL checkpointer
tools/flight_tool.py   AviationStack flight search
 tools/tavily_tool.py  Tavily hotel and web search
static/                Frontend assets
templates/             HTML frontend
Dockerfile             Container image definition
```

## Troubleshooting

- `GROQ_API_KEY is missing`: check the `.env` file and variable spelling.
- PostgreSQL connection errors in Docker: replace `localhost` with `host.docker.internal` when PostgreSQL runs on the host.
- Docker rejects the env file: remove spaces around variable names, for example use `LANGSMITH_API_KEY=value`.
- No flight results: confirm the AviationStack key and route details.

## Development Test

`test.py` runs an interactive request against the configured services:

```powershell
python test.py
```

The FastAPI root endpoint can be checked without calling external APIs:

```powershell
Invoke-WebRequest http://localhost:8000/
```
