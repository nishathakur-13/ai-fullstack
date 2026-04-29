import json
import os
import re

from groq import Groq
from dotenv import load_dotenv

from backend.ai.prompts import SYSTEM_PROMPT

load_dotenv()


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


def extract_json(text):

    text = text.strip()

    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if match:
        return match.group(0)

    return text


def analyze_complaint(complaint_text):

    user_prompt = f"""
    Analyze this complaint.

    Complaint:
    {complaint_text}

    Return ONLY valid JSON.
    """

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],

        temperature=0
    )

    content = (
        response.choices[0]
        .message.content
    )

    cleaned = extract_json(content)

    parsed = json.loads(cleaned)

    return {

        "complaint": complaint_text,

        "urgency": parsed.get(
            "urgency",
            "UNKNOWN"
        ),

        "department": parsed.get(
            "department",
            "UNKNOWN"
        ),

        "estimated_resolution_time": parsed.get(
            "estimated_resolution_time",
            "UNKNOWN"
        ),

        "explanation": parsed.get(
            "explanation",
            "No explanation"
        ),

        "detected_location": parsed.get(
            "detected_location",
            "Haldwani"
        )
    }
