from fastapi import FastAPI
from app.routers import volumes, health

app = FastAPI(title="Opsguardian")

app.include_router(health.router)
app.include_router(volumes.router)