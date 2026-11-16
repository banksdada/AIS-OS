from __future__ import annotations

import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import knowledge, llm
from .config import Settings, load_settings
from .leads import record_lead
from .tidycal import SlotUnavailable, TidyCalClient, TidyCalError, display_slot

BOOKING_HINTS = ("book", "call", "meeting", "slot", "available", "schedule", "talk")
WIDGET = Path(__file__).resolve().parent.parent / "widget" / "widget.js"


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class BookIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=200)
    starts_at: str = Field(min_length=10, max_length=40)


class LeadIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=200)
    question: str = Field(min_length=1, max_length=2000)


class Limiter:
    def __init__(self, per_minute: int = 20) -> None:
        self.per_minute = per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > 60:
            bucket.popleft()
        if len(bucket) >= self.per_minute:
            return False
        bucket.append(now)
        return True


def _client(settings: Settings) -> TidyCalClient:
    return TidyCalClient(settings.tidycal_token, settings.booking_type_id, settings.user_agent)


def _wants_booking(message: str) -> bool:
    lowered = message.lower()
    return any(word in lowered for word in BOOKING_HINTS)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="WebAwesome Site Agent", version="0.1.0")
    app.state.settings = settings
    app.state.limiter = Limiter()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    def guard(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        if not app.state.limiter.allow(ip):
            raise HTTPException(status_code=429, detail="Too many requests, slow down.")

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "tidycal_configured": bool(settings.tidycal_token and settings.booking_type_id),
            "llm_configured": bool(settings.openai_api_key),
            "knowledge_docs": len(knowledge.load_docs()),
        }

    @app.get("/widget.js")
    def widget_js() -> FileResponse:
        if not WIDGET.exists():
            raise HTTPException(status_code=404, detail="widget not bundled")
        return FileResponse(
            WIDGET,
            media_type="application/javascript",
            headers={"Cache-Control": "public, max-age=300"},
        )

    @app.get("/slots")
    def slots(request: Request, limit: int = 3) -> dict[str, object]:
        guard(request)
        limit = max(1, min(limit, 10))
        try:
            return {"slots": _client(settings).available_slots(limit=limit)}
        except TidyCalError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/chat")
    def chat(body: ChatIn, request: Request) -> dict[str, object]:
        guard(request)
        context = knowledge.build_context(body.message)
        try:
            reply = llm.answer(
                body.message,
                context,
                api_key=settings.openai_api_key,
                model=settings.openai_model,
            )
        except llm.LLMError:
            reply = llm.fallback(context)
        payload: dict[str, object] = {"reply": reply}
        if _wants_booking(body.message):
            try:
                payload["slots"] = _client(settings).available_slots(limit=3)
            except TidyCalError:
                payload["slots"] = []
        return payload

    @app.post("/book")
    def book(body: BookIn, request: Request) -> dict[str, object]:
        guard(request)
        if "@" not in body.email:
            raise HTTPException(status_code=422, detail="A valid email is required.")
        try:
            data = _client(settings).create_booking(
                name=body.name, email=body.email, starts_at=body.starts_at
            )
        except SlotUnavailable:
            try:
                fresh = _client(settings).available_slots(limit=3)
            except TidyCalError:
                fresh = []
            raise HTTPException(
                status_code=409,
                detail={"message": "That slot was just taken.", "slots": fresh},
            ) from None
        except TidyCalError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {
            "booking_id": data.get("id"),
            "starts_at": data.get("starts_at"),
            "label": display_slot(data["starts_at"]) if data.get("starts_at") else None,
        }

    @app.post("/lead")
    def lead(body: LeadIn, request: Request) -> dict[str, object]:
        guard(request)
        if "@" not in body.email:
            raise HTTPException(status_code=422, detail="A valid email is required.")
        return record_lead(
            settings, name=body.name, email=body.email, question=body.question
        )

    return app


app = create_app()
