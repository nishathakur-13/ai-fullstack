from pydantic import BaseModel


class ComplaintRequest(BaseModel):

    text: str

    location: str


class ComplaintResponse(BaseModel):

    complaint: str

    urgency: str

    department: str

    estimated_resolution_time: str

    explanation: str