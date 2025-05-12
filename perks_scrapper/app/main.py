from fastapi import FastAPI, HTTPException, BackgroundTasks
import uvicorn
import os

from .models import PerkUpdateRequest, AggregatedPerkInfo
from .services import process_perk_update, OPENAI_API_KEY, FIRECRAWL_API_KEY, EXA_API_KEY, AIRTABLE_API_KEY

app = FastAPI(
    title="Perks Scraper Agent",
    description="An AI agent to scrape, analyze, and update startup perk information in Airtable.",
    version="0.1.0"
)

# Simple check for essential API keys on startup
if not all([OPENAI_API_KEY, FIRECRAWL_API_KEY, EXA_API_KEY, AIRTABLE_API_KEY]):
    print("ERROR: One or more essential API keys are missing. Check your .env file.")
    # Depending on deployment strategy, you might want to raise an Exception
    # raise RuntimeError("API Keys missing, cannot start application.")

@app.post("/update-perk", response_model=AggregatedPerkInfo)
async def update_perk_endpoint(request: PerkUpdateRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to trigger the perk update process for a given Airtable record ID.
    This endpoint immediately returns a confirmation and runs the actual process
    in the background to avoid timeouts for long-running scraping/analysis tasks.
    (Note: For simplicity, it currently runs synchronously. Refactor needed for true background.)
    """
    print(f"Received request to update perk for Airtable record: {request.airtable_record_id}")

    # --- Synchronous Execution (for simplicity in this example) ---
    # For a real application, especially with multiple requests, use BackgroundTasks:
    # background_tasks.add_task(process_perk_update, request.airtable_record_id)
    # return {"message": "Perk update process started in background.", "record_id": request.airtable_record_id}
    # However, BackgroundTasks doesn't easily allow returning the final result.
    # Proper async handling might involve task queues (Celery, RQ) or WebSocket updates.

    try:
        result = await process_perk_update(request.airtable_record_id)
        return result
    except Exception as e:
        # Catch unexpected errors during processing
        print(f"Unhandled exception during perk update for {request.airtable_record_id}: {e}")
        # Log the full traceback here in a real application
        raise HTTPException(status_code=500, detail=f"Internal server error processing record {request.airtable_record_id}")

@app.get("/")
async def root():
    return {"message": "Perks Scraper Agent is running. POST to /update-perk with Airtable record ID."}

# Add command to run the app easily if needed (e.g., for local testing)
# This part is typically handled by uvicorn command line directly
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 