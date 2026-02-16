from fastapi import FastAPI
from app.routers import volumes, health, security

app = FastAPI(title="Opsguardian")

app.include_router(health.router)
app.include_router(volumes.router)
app.include_router(security.router)