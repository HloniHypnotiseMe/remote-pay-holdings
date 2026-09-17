#!/usr/bin/env python3
"""
Human Override API
Required by King V: Human oversight of AI systems.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import json

app = FastAPI(title="C6 Human Override API")

PENDING_REVIEWS = []
APPROVED_ACTIONS = []


class ReviewRequest(BaseModel):
    agent_name: str
    action: str
    payload: dict
    risk_score: float
    reason: str


class OverrideDecision(BaseModel):
    review_id: int
    decision: str  # "approve", "reject", "modify"
    human_notes: str
    modified_payload: dict = None


@app.post("/review/request")
def request_review(req: ReviewRequest):
    """Agent requests human approval for high-risk action."""
    review = {
        "id": len(PENDING_REVIEWS) + 1,
        "agent": req.agent_name,
        "action": req.action,
        "payload": req.payload,
        "risk_score": req.risk_score,
        "reason": req.reason,
        "status": "PENDING",
        "requested_at": datetime.now().isoformat()
    }
    PENDING_REVIEWS.append(review)
    return {"review_id": review["id"], "status": "queued"}


@app.get("/review/pending")
def get_pending():
    """Human views pending reviews."""
    return [r for r in PENDING_REVIEWS if r["status"] == "PENDING"]


@app.post("/review/decide")
def decide(decision: OverrideDecision):
    """Human makes a decision."""
    for review in PENDING_REVIEWS:
        if review["id"] == decision.review_id:
            review["status"] = decision.decision.upper()
            review["human_notes"] = decision.human_notes
            review["decided_at"] = datetime.now().isoformat()

            if decision.decision == "approve":
                APPROVED_ACTIONS.append(review)
                return {"status": "approved", "action_executed": True}
            elif decision.decision == "reject":
                return {"status": "rejected", "action_executed": False}
            elif decision.decision == "modify":
                review["payload"] = decision.modified_payload
                APPROVED_ACTIONS.append(review)
                return {"status": "modified", "action_executed": True}

    raise HTTPException(404, "Review not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
