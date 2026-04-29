import os

from supabase import create_client
from dotenv import load_dotenv

from backend.utils.geocoder import (
    get_coordinates
)

load_dotenv()

SUPABASE_URL = os.getenv(
    "SUPABASE_URL"
)

SUPABASE_KEY = os.getenv(
    "SUPABASE_KEY"
)

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


def save_complaint(data):

    location_text = data.get(
    "location",
    "Haldwani"
)

    print("\nDETECTED LOCATION:")
    print(location_text)

    coords = get_coordinates(
        location_text
    )

    print("\nCOORDINATES:")
    print(coords)

    response = (

        supabase.table("complaints")

        .insert({

            "complaint_text":
            data["complaint"],

            "urgency":
            data["urgency"],

            "department":
            data["department"],

            "eta":
            data[
                "estimated_resolution_time"
            ],

            "explanation":
            data["explanation"],

            "status":
            "pending",

            "latitude":
            coords["latitude"],

            "longitude":
            coords["longitude"]

        })

        .execute()
    )

    return response


def get_complaints():

    response = (

        supabase.table("complaints")

        .select("*")

        .order(
            "created_at",
            desc=True
        )

        .execute()
    )

    return response.data