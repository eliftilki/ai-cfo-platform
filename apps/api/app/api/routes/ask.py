from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps.auth import get_current_user_context
from app.connectors.agent_service_client import AgentServiceError
from app.services.ask_service import run_ask_flow
from packages.contracts.python.analysis_contracts import AskRequest, AskResponse
from packages.contracts.python.auth_contracts import MeResponse


router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask_ai_cfo(
    request: AskRequest,
    current_user: MeResponse = Depends(get_current_user_context),
):
    """Handle ask ai cfo requests from the web app."""
    try:
        return run_ask_flow(
            company_id=current_user.company_id,
            question=request.question,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except AgentServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ask flow failed: {str(exc)}")