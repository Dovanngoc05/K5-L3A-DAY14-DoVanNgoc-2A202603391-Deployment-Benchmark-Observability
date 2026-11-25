"""
Production AI Agent — Part 6 Final Project (bản khung)

Hoàn thành các TODO để đạt đủ 12 tiêu chí trong README.md, rồi kiểm tra:
    python check_production_ready.py

Bản khung này chạy được (uvicorn app.main:app) nhưng chưa đạt tiêu chí nào.
"""
import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_budget, record_cost
from app.rate_limiter import check_rate_limit
from app.redis_client import redis_healthy
from utils.mock_llm import ask as llm_ask


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "ts": self.formatTime(record),
            "lvl": record.levelname,
            "event": record.getMessage(),
        })


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger("agent")
logger.setLevel(logging.INFO)
logger.handlers = [handler]
logger.propagate = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup")
    yield
    logger.info("shutdown")


app = FastAPI(title="Production AI Agent", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    user_id: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    if not redis_healthy():
        raise HTTPException(status_code=503, detail="Redis unavailable")
    return {"ready": True}


@app.post("/ask")
def ask(body: AskRequest, key: str = Depends(verify_api_key)):
    check_rate_limit(key)
    check_budget()

    answer = llm_ask(body.question)
    input_tokens = max(1, len(body.question.split()) * 2)
    output_tokens = max(1, len(answer.split()) * 2)
    cost = record_cost(input_tokens, output_tokens)

    logger.info("request_completed")
    return {
        "question": body.question,
        "answer": answer,
        "cost_usd": cost,
    }