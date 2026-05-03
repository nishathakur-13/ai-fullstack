# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models.schemas import (
    ComplaintRequest,
    ComplaintResponse
)

from langgraph_workflow import app as langgraph_app

from backend.db.supabase_client import (
    save_complaint,
    get_complaints
)

app = FastAPI()


# ------------------------------------------------
# CORS
# ------------------------------------------------

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ------------------------------------------------
# Root Endpoint
# ------------------------------------------------

@app.get("/")
def root():

    return {
        "message": (
            "AI Complaint Prioritization API Running"
        )
    }


# ------------------------------------------------
# Analyze Complaint Endpoint
# ------------------------------------------------

@app.post(
    "/analyze",
    response_model=ComplaintResponse
)
async def analyze(
    data: ComplaintRequest
):

    result = langgraph_app.invoke({
        "complaint": data.text,
        "location": data.location
    })

    final_result = result["final"]


    # ------------------------------------------------
    # Ensure department is never empty
    # ------------------------------------------------

    if not final_result.get("department"):

        final_result["department"] = (
            "General Administration"
        )


    # ------------------------------------------------
    # Save complaint
    # ------------------------------------------------

    save_complaint(final_result)


    # ------------------------------------------------
    # Return response
    # ------------------------------------------------

    return final_result


# ------------------------------------------------
# Get Complaint History
# ------------------------------------------------

@app.get("/complaints")
async def fetch_complaints():

    try:

        data = get_complaints()

        return data

    except Exception as e:

        print("\nFETCH ERROR:\n")
        print(str(e))

        return []

@app.get("/ping")
def ping():
    return {"status": "alive"}
