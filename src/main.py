from fastapi import FastAPI
from .routes import router

app = FastAPI(title="Agentic Deploy (Anthropic)", version="0.2.0")
app.include_router(router)
