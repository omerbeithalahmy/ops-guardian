import os

class Settings:
    AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

settings = Settings()