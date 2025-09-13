from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.routes import trip

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="AI Trip Planner")

# Register routes
app.include_router(trip.router, prefix="/trip", tags=["Trip"])

@app.get("/")
def root():
    return {"message": "Trip Planner Backend is running 🚀"}