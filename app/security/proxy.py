"""Local OAuth metadata validation helper used as a security proxy boundary."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.security.url_sanitizer import validate_authorization_endpoint

router = APIRouter(prefix="/api/security", tags=["Security Assessment"])

class EndpointRequest(BaseModel):
    authorization_endpoint: str = Field(min_length=1, max_length=4096)

@router.post("/validate-authorization-endpoint")
def validate_endpoint(payload: EndpointRequest):
    result = validate_authorization_endpoint(payload.authorization_endpoint)
    if not result["allowed"]:
        raise HTTPException(status_code=400, detail={
            "blocked": True,
            "case_study": "CVE-2025-6514",
            "reason": result["reason"],
        })
    return {"blocked": False, "case_study": "CVE-2025-6514", **result}
