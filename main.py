import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
import logging
import requests

from schemas import Enquiry, CaseStudy
from database import create_document, get_documents, db

app = FastAPI(title="L&D Backend API")

# CORS (open for dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ld-api")


@app.get("/")
def read_root():
    return {"message": "L&D Backend Running", "time": datetime.now(timezone.utc).isoformat()}


@app.get("/test")
def test_database():
    """Check database connectivity and list collections."""
    resp = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if os.getenv("DATABASE_URL"):
            resp["database_url"] = "✅ Set"
        if os.getenv("DATABASE_NAME"):
            resp["database_name"] = "✅ Set"
        if db is not None:
            resp["database"] = "✅ Available"
            try:
                resp["collections"] = db.list_collection_names()
                resp["connection_status"] = "Connected"
                resp["database"] = "✅ Connected & Working"
            except Exception as e:
                resp["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
    except Exception as e:
        resp["database"] = f"❌ Error: {str(e)[:80]}"
    return resp


# -------- Email helper (SendGrid REST) --------
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL", NOTIFY_EMAIL or "no-reply@example.com")


def send_notification_email(enquiry: Enquiry) -> bool:
    """Send an email via SendGrid if API key and recipient are configured.
    Returns True if attempted and accepted, False if skipped or failed.
    """
    if not SENDGRID_API_KEY or not NOTIFY_EMAIL or not FROM_EMAIL:
        logger.info("Email notification skipped: missing SENDGRID_API_KEY/NOTIFY_EMAIL/FROM_EMAIL")
        return False

    subject = f"New L&D Enquiry from {enquiry.name}"
    text = (
        f"Name: {enquiry.name}\n"
        f"Email: {enquiry.email}\n"
        f"Phone: {enquiry.phone or '-'}\n"
        f"Company: {enquiry.company or '-'}\n"
        f"Service: {enquiry.service or '-'}\n"
        f"Consent: {enquiry.consent}\n"
        f"Source: {enquiry.source or '-'}\n\n"
        f"Message:\n{enquiry.message}\n"
    )
    payload = {
        "personalizations": [{"to": [{"email": NOTIFY_EMAIL}]}],
        "from": {"email": FROM_EMAIL, "name": "L&D Website"},
        "subject": subject,
        "content": [{"type": "text/plain", "value": text}],
    }
    try:
        r = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=8,
        )
        if 200 <= r.status_code < 300:
            logger.info("SendGrid accepted email notification")
            return True
        logger.warning(f"SendGrid rejected email: {r.status_code} {r.text}")
        return False
    except Exception as e:
        logger.error(f"SendGrid error: {e}")
        return False


# -------- Enquiries --------
@app.get("/enquiries")
def list_enquiries(limit: Optional[int] = 100):
    try:
        docs = get_documents("enquiry", {}, limit)
        # Convert ObjectId and datetime to strings
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
            for k in ("created_at", "updated_at"):
                if k in d and hasattr(d[k], "isoformat"):
                    d[k] = d[k].isoformat()
        return {"items": docs, "count": len(docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/enquiries", status_code=201)
def create_enquiry(enquiry: Enquiry):
    try:
        new_id = create_document("enquiry", enquiry)
        # Fire-and-forget email (best-effort)
        send_notification_email(enquiry)
        return {"id": new_id, "status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------- Case studies --------
DEFAULT_CASE_STUDIES: List[CaseStudy] = [
    CaseStudy(
        title="Leadership capability uplift in NHS Trust",
        client="NHS Trust (North of England)",
        sector="NHS",
        challenge="Inconsistent people leadership at Band 6–8a impacting patient flow and staff engagement",
        approach="Blended programme (ILM Level 5-aligned) with action learning sets, coaching, and on-the-job projects",
        outcomes=[
            "12% improvement in staff engagement index",
            "8% reduction in short-term sickness",
            "Faster escalation and decision-making on wards",
        ],
        quote="The programme has transformed how our middle managers lead day-to-day.",
        quote_author="Deputy Director of HR",
    ),
    CaseStudy(
        title="Operational excellence in Local Authority services",
        client="Metropolitan Borough Council",
        sector="Local Government",
        challenge="Service backlogs and low morale across customer services",
        approach="Leadership & management fundamentals (CMI Level 3-aligned) and coaching for team leaders",
        outcomes=[
            "Average case closure time reduced by 22%",
            "CSAT improved from 71% to 84%",
            "First-line resolution up by 15%",
        ],
        quote="Clear, practical, and tailored to our context.",
        quote_author="Head of Customer Services",
    ),
]


@app.get("/case-studies")
def get_case_studies():
    # Serve defaults without requiring DB; if you want to persist edits, you can add DB storage later
    return {"items": [cs.model_dump() for cs in DEFAULT_CASE_STUDIES]}


# -------- Accreditations --------
class Accreditation(BaseModel):
    body: str
    levels: List[str]
    description: str
    badges: List[str]  # URLs to images (frontend can use placeholders)


@app.get("/accreditations")
def get_accreditations():
    return {
        "items": [
            Accreditation(
                body="ILM",
                levels=["Level 3", "Level 5", "Level 7"],
                description="Programmes aligned to ILM standards with practical assessment and work-based learning",
                badges=["/ilm-badge.svg"],
            ).model_dump(),
            Accreditation(
                body="CMI",
                levels=["Level 3", "Level 5"],
                description="Management and leadership pathways mapped to the CMI Professional Standard",
                badges=["/cmi-badge.svg"],
            ).model_dump(),
            Accreditation(
                body="Apprenticeships",
                levels=["Team Leader/Supervisor L3", "Operations/Departmental Manager L5"],
                description="Alignment to apprenticeship standards and off-the-job training requirements",
                badges=["/apprenticeship-badge.svg"],
            ).model_dump(),
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
