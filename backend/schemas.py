from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Each model corresponds to a MongoDB collection named after the lowercase class name
# e.g., class Enquiry -> collection "enquiry"

class Enquiry(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    message: Optional[str] = Field(default="", max_length=5000)
