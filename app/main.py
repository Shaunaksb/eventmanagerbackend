from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import time
import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.config import settings

logging.basicConfig(filename='debug.log', level=logging.DEBUG)

app = FastAPI(
    title="Corporate Event Management API",
    openapi_url=f"/api/v1/openapi.json"
)

@app.on_event("startup")
async def startup_event():
    max_retries = 5
    retries = 0
    while retries < max_retries:
        try:
            engine = create_async_engine(settings.DATABASE_URL)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            break
        except OperationalError:
            retries += 1
            time.sleep(5)
    if retries == max_retries:
        raise Exception("Could not connect to the database")

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")