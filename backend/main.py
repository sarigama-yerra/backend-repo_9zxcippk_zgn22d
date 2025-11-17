from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from schemas import Enquiry
from database import create_document, get_documents

app = FastAPI(title="L&D UK API")

# Allow local and preview origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EnquiryResponse(BaseModel):
    id: str
    name: str
    email: str
    message: str | None = None
    created_at: str

@app.get("/")
async def root():
    return {"status": "ok", "service": "ld-uk"}

@app.get("/enquiries")
async def list_enquiries(limit: int = 50):
    items = await get_documents("enquiry", {}, limit)
    return items

@app.post("/enquiries", response_model=EnquiryResponse)
async def create_enquiry(payload: Enquiry):
    try:
        saved = await create_document("enquiry", payload.dict())
        return {
            "id": saved.get("_id"),
            "name": saved.get("name"),
            "email": saved.get("email"),
            "message": saved.get("message"),
            "created_at": saved.get("created_at"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
async def test_db():
    # Smoke test DB connectivity by listing 1 document
    items = await get_documents("enquiry", {}, 1)
    return {"ok": True, "sample": items}
