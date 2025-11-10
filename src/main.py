from typing import Union
from contextlib import asynccontextmanager
from api.db.session import init_db
from fastapi import FastAPI
from api.v1.books.routing import router as books_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # before app startup up
    init_db()
    yield
    # clean up

app = FastAPI(lifespan=lifespan)
app.include_router(books_router, prefix="/api/v1/books",)

@app.get("/health")
def read_health():
    return {"status": "ok"}