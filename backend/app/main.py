from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.models import Student, Dictation, Submission, Mistake

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Database initialized.")
    yield

app = FastAPI(
    title="Projet Rousseau",
    version="1.0.0",
    description="API for Projet Rousseau application.",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Projet Rousseau API!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}