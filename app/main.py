from fastapi import FastAPI
from app.routers import health, costs, security, hygiene, network

app = FastAPI(title="Opsguardian")

app.include_router(health.router)
app.include_router(costs.router)
app.include_router(security.router)
app.include_router(hygiene.router)
app.include_router(network.router)