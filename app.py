from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Travel AI Assistant")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class ChatRequest(BaseModel):
	message: str
	thread_id: str | None = None


@app.get("/", include_in_schema=False)
async def home():
	return FileResponse(BASE_DIR / "templates" / "index.html")


@app.post("/chat")
async def chat(request: ChatRequest):
	if not request.message.strip():
		raise HTTPException(status_code=422, detail="Message cannot be empty.")

	try:
		from backend import run_travel_agent

		return await run_in_threadpool(
			run_travel_agent,
			request.message.strip(),
			request.thread_id,
		)
	except Exception as exc:
		raise HTTPException(
			status_code=502,
			detail="The travel assistant could not complete this request.",
		) from exc
