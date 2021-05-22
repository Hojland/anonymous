import json
import sys
from pathlib import Path

from botocore.exceptions import ClientError
from cachetools import LRUCache, cached
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from models.model import Anonymous

from settings import settings
from utils import data_utils

app = FastAPI()
cache = LRUCache(maxsize=4)


class TextInput(BaseModel):
    text: str = Field(None, title="The text to anynomize")


class TextOutput(BaseModel):
    text: str = Field(None, title="The anonymized text")


class HealthResponse(BaseModel):
    ready: bool


@app.post("/anonymize", response_model=TextOutput)
async def predict(in_text: TextInput):

    # Fetch model
    model = get_model()

    # Predict on text
    out_text = model.anonymize(in_text)

    # Return prediction result
    res = TextOutput(text=out_text)
    return res


@app.get("/health")
async def get_health(response: Response):
    status = await get_health_info()
    response.status_code = 200 if status.ready else 503
    return status


@app.get("/clear_cache")
async def clear_cache():
    cache.clear()
    return True


async def get_health_info() -> HealthResponse:
    # do checks
    ready = True
    return HealthResponse(ready=ready)


@cached(cache=cache)
def get_model():
    model = Anonymous()
    return model
