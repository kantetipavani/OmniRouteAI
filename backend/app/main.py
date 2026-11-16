"""
Main entry point for OmniRoute Backend API.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging

from app.api.endpoints import api_router
from app.database import get_collection
from app.services.generator import SyntheticDataGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("omniroute")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Check if DB is empty; if so, populate starter dataset automatically
    db_tickets = get_collection("tickets")
    if db_tickets.count_documents({}) == 0:
        logger.info("Initializing baseline starter dataset (seed: 20261022)...")
        gen = SyntheticDataGenerator(seed=20261022)
        data = gen.generate_all(scale="starter")
        gen.export_to_disk(data, output_dir="backend/data")

        collections_to_load = [
            ("customers", data["customers"]),
            ("channels", data["channels"]),
            ("languages", data["languages"]),
            ("skills", data["skills"]),
            ("queues", data["queues"]),
            ("intents", data["intents"]),
            ("priority_rules", data["priority_rules"]),
            ("agents", data["agents"]),
            ("tickets", data["tickets"]),
            ("messages", data["messages"]),
            ("assignment_events", data["assignment_events"]),
            ("sla_events", data["sla_events"]),
            ("resolutions", data["resolutions"]),
            ("ground_truth", data["ground_truth"])
        ]
        for col_name, records in collections_to_load:
            col = get_collection(col_name)
            col.delete_many({})
            if records:
                col.insert_many([dict(r) for r in records])
        logger.info("Baseline starter dataset initialized successfully. Tickets: %d, Anomalies: %d", len(data["tickets"]), len(data["ground_truth"]))
    yield

app = FastAPI(
    title="OmniRoute Intelligent Case Routing & SLA Engine",
    description="Enterprise routing of email, chat, and phone cases by intent, urgency, language, skill, and agent capacity with SLA tracking.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Mount compiled React frontend if present
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
else:
    @app.get("/")
    def health_check():
        return {
            "service": "OmniRoute Case Routing & SLA Engine",
            "status": "HEALTHY",
            "version": "1.0.0",
            "docs_url": "/docs"
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=True)
