import threading
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import health, costs, security, hygiene, network
from app.services import slack, slack_listener

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("opsguardian")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting OpsGuardian Bolt listener...")
    thread = threading.Thread(target=slack_listener.start_slack_listener, daemon=True)
    thread.start()
    yield
    logger.info("Stopping OpsGuardian...")

app = FastAPI(title="Opsguardian", lifespan=lifespan)

@app.get("/slack/control", tags=["Slack"])
def send_slack_control():
    slack.send_control_center()
    return {"message": "Control center message sent to Slack"}

app.include_router(health.router)
app.include_router(costs.router)
app.include_router(security.router)
app.include_router(hygiene.router)
app.include_router(network.router)