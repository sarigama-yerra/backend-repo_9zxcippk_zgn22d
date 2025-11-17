"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" (example)
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict

# Existing example schemas (kept for reference)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    address: Optional[str] = Field(None, description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in GBP")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# L&D website schemas
class Enquiry(BaseModel):
    name: str = Field(..., description="Full name of the enquirer")
    email: EmailStr = Field(..., description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    company: Optional[str] = Field(None, description="Company/organisation")
    service: Optional[str] = Field(
        None,
        description="Service interest (e.g., Workforce Development, Leadership & Management, Coaching & Mentoring, Training Strategy)",
    )
    message: str = Field(..., min_length=5, description="Free-text enquiry message")
    consent: Optional[bool] = Field(False, description="GDPR consent to be contacted")
    source: Optional[str] = Field(None, description="Where enquiry came from (site, campaign, etc.)")

class CaseStudy(BaseModel):
    title: str
    client: str
    sector: str
    challenge: str
    approach: str
    outcomes: List[str]
    quote: Optional[str] = None
    quote_author: Optional[str] = None
    metrics: Optional[Dict[str, str]] = None
