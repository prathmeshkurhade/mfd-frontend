"""
PDF Generation Routes
"""

from uuid import UUID
from io import BytesIO
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.auth.dependencies import get_current_user_id
from app.services.pdf_service import PDFService


router = APIRouter(prefix="/pdfs", tags=["PDFs"])


class PDFResponse(BaseModel):
    pdf_url: str


# =============================================================================
# PDF INPUT MODELS (Calculator Results)
# =============================================================================

class LoanDetailsInput(BaseModel):
    loan_amount: float
    interest_rate: float
    tenure_months: int
    emi: float
    total_interest: float
    total_payment: float
    loan_type: str

class GoldCalculatorResultInput(BaseModel):
    """Gold Calculator Result for PDF generation"""
    calculator_type: str = "gold"
    calculation_mode: str
    weighted_return: float
    supports_monthly: bool = True
    purpose: str
    purity: str
    quantity_grams: float
    purity_percentage: float
    current_price_per_gram: float
    current_target_value: float
    future_target_value: float
    years_to_goal: int = 3
    required_monthly: Optional[float] = None
    required_yearly: Optional[float] = None
    required_lumpsum: Optional[float] = None
    investment_amount: Optional[float] = None
    investment_frequency: Optional[str] = None
    projected_corpus: Optional[float] = None
    corpus_covers_percent: Optional[float] = None
    gap_amount: Optional[float] = None
    loan_details: Optional[LoanDetailsInput] = None
    total_monthly_outflow: Optional[float] = None
    investment_options: Optional[Dict[str, Any]] = None
    product_breakdown: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        extra = "allow"


# =============================================================================
# CALCULATOR PDF ENDPOINTS
# =============================================================================

@router.post("/calculator/gold/test", summary="Test Gold PDF (No Auth)")
async def test_gold_calculator_pdf(
    calculator_result: GoldCalculatorResultInput,
    client_name: str = Query("Valued Client"),
    advisor_name: str = Query("Financial Advisor"),
):
    """Generate PDF from calculator result - No auth for testing."""
    service = PDFService()
    try:
        pdf_bytes = await service.generate_gold_calculator_pdf(
            calculator_response=calculator_result.model_dump(mode="json"),
            client_name=client_name,
            advisor_name=advisor_name,
        )
        
        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=gold_investment_report.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# EXISTING ENDPOINTS (stubs)
# =============================================================================

@router.post("/goal/{goal_id}", response_model=PDFResponse)
async def generate_goal_pdf(
    goal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Generate PDF for a goal."""
    service = PDFService(user_id)
    try:
        pdf_url = await service.generate_goal_pdf(goal_id)
        return PDFResponse(pdf_url=pdf_url)
    except NotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/touchpoint/{touchpoint_id}/mom", response_model=PDFResponse)
async def generate_mom_pdf(
    touchpoint_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Generate Minutes of Meeting PDF for a touchpoint."""
    service = PDFService(user_id)
    try:
        pdf_url = await service.generate_mom_pdf(touchpoint_id)
        return PDFResponse(pdf_url=pdf_url)
    except NotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/calculator/{result_id}", response_model=PDFResponse)
async def generate_calculator_pdf(
    result_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Generate PDF for saved calculator result."""
    service = PDFService(user_id)
    try:
        pdf_url = await service.generate_calculator_pdf(result_id)
        return PDFResponse(pdf_url=pdf_url)
    except NotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/client/{client_id}/report", response_model=PDFResponse)
async def generate_client_report(
    client_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    """Generate comprehensive client portfolio report."""
    service = PDFService(user_id)
    try:
        pdf_url = await service.generate_client_report(client_id)
        return PDFResponse(pdf_url=pdf_url)
    except NotImplementedError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))