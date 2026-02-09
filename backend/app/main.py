from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from fastapi.middleware.cors import CORSMiddleware
from backend.app.services import stats_service

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

origins = [
    "http://localhost:5173",    # Front-End.
    "http://localhost:8080",    # Autre port fréquent.
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Projet Rousseau API!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

app.include_router(stats_service.router, prefix="/api/stats", tags=["Stats"])