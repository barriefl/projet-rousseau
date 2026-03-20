from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.endpoints import (
    assessment_import_endpoint,
    auth_endpoint,
    categories_endpoint,
    dictations_endpoint,
    groups_endpoint,
    import_endpoint,
    promotions_endpoint,
    rules_endpoint,
    stats_endpoint,
    students_endpoint,
    submissions_endpoint,
    tools_endpoint,
)
from app.utils.auth import verify_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Database initialized.")
    yield


app = FastAPI(
    title="Projet Rousseau",
    version="1.0.0",
    description="API for Projet Rousseau application.",
    lifespan=lifespan,
)

origins = [
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "https://emmanuellegraziano.alwaysdata.net"
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


app.include_router(auth_endpoint.router, prefix="/api")
app.include_router(
    promotions_endpoint.router, prefix="/api", dependencies=[Depends(verify_token)]
)
app.include_router(
    tools_endpoint.router, prefix="/api", dependencies=[Depends(verify_token)]
)
app.include_router(
    groups_endpoint.router, prefix="/api", dependencies=[Depends(verify_token)]
)
app.include_router(
    import_endpoint.router, prefix="/api", dependencies=[Depends(verify_token)]
)
app.include_router(
    assessment_import_endpoint.router,
    prefix="/api",
    dependencies=[Depends(verify_token)],
)
app.include_router(
    dictations_endpoint.router,
    prefix="/api",
    dependencies=[Depends(verify_token)],
)
app.include_router(
    students_endpoint.router,
    prefix="/api",
    dependencies=[Depends(verify_token)],
)
app.include_router(
    submissions_endpoint.router,
    prefix="/api",
    dependencies=[Depends(verify_token)],
)
app.include_router(
    categories_endpoint.router, prefix="/api", dependencies=[Depends(verify_token)]
)
app.include_router(
    rules_endpoint.router,
    prefix="/api",
    dependencies=[Depends(verify_token)],
)
app.include_router(
    stats_endpoint.router,
    prefix="/api",
    dependencies=[Depends(verify_token)],
)
