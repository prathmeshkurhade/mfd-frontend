"""
Calculator Routes
FastAPI endpoints for all 10 calculators.
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.calculator import (
    # Requests
    SIPLumpsumGoalRequest,
    VehicleCalculatorRequest,
    VacationCalculatorRequest,
    EducationCalculatorRequest,
    WeddingCalculatorRequest,
    GoldCalculatorRequest,
    RetirementCalculatorRequest,
    SWPCalculatorRequest,
    PrepaymentCalculatorRequest,
    CashSurplusCalculatorRequest,
    # Responses
    SIPLumpsumGoalResponse,
    VehicleCalculatorResponse,
    VacationCalculatorResponse,
    EducationCalculatorResponse,
    WeddingCalculatorResponse,
    GoldCalculatorResponse,
    RetirementCalculatorResponse,
    SWPCalculatorResponse,
    PrepaymentCalculatorResponse,
    CashSurplusCalculatorResponse,
    CalculatorAPIResponse,
    CalculatorResultSave,
)

from app.services.calculator_service import calculator_service


router = APIRouter(prefix="/calculators", tags=["Calculators"])


# =============================================================================
# 1. SIP / LUMPSUM / GOAL UNIFIED CALCULATOR
# =============================================================================

@router.post("/sip-lumpsum-goal", response_model=SIPLumpsumGoalResponse, summary="SIP/Lumpsum/Goal Calculator")
async def calculate_sip_lumpsum_goal(request: SIPLumpsumGoalRequest):
    """
    Unified calculator for SIP, Lumpsum, and Goal-based planning.
    
    **Modes:**
    - `sip`: Calculate corpus from monthly SIP amount
    - `lumpsum`: Calculate corpus from one-time investment
    - `goal_sip`: Calculate required monthly SIP for a target
    - `goal_lumpsum`: Calculate required lumpsum for a target
    - `goal_both`: Show both SIP and lumpsum options for a target
    
    **Features:**
    - Step-up SIP (₹ amount or % increase)
    - Inflation-adjusted goals
    - Existing savings consideration
    - Investment-based mode with gap loan
    
    **Examples:**
    - Mode `sip`: "I invest ₹10K/month for 15 years" → Get expected corpus
    - Mode `goal_both`: "I need ₹50L in 10 years" → Get required SIP and lumpsum options
    """
    try:
        return calculator_service.calculate_sip_lumpsum_goal(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 2. VEHICLE CALCULATOR
# =============================================================================

@router.post("/vehicle", response_model=VehicleCalculatorResponse, summary="Vehicle Calculator")
async def calculate_vehicle(request: VehicleCalculatorRequest):
    """
    Plan vehicle purchase with down payment and loan.
    
    **Supports:**
    - Cars and Bikes
    - Future price with inflation
    - Down payment investment planning
    - Vehicle loan EMI calculation
    - Total cost of ownership
    
    **Dual Mode:**
    - `target_based`: Get required SIP for down payment
    - `investment_based`: See what you can afford + loan for gap
    """
    try:
        return calculator_service.calculate_vehicle(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 3. VACATION CALCULATOR
# =============================================================================

@router.post("/vacation", response_model=VacationCalculatorResponse, summary="Vacation Calculator")
async def calculate_vacation(request: VacationCalculatorRequest):
    """
    Plan vacation savings with destination-based pricing.
    
    **Features:**
    - Pre-defined destinations (Dubai, Paris, Goa, etc.)
    - Package types: Standard, Premium, Business
    - Per-person pricing
    - Inflation-adjusted future cost
    - Price breakdown (flights, hotels, activities, etc.)
    - Affordability check
    
    **Dual Mode:**
    - `target_based`: Get required SIP for trip
    - `investment_based`: See projected savings + travel loan
    """
    try:
        return calculator_service.calculate_vacation(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 4. EDUCATION CALCULATOR
# =============================================================================

@router.post("/education", response_model=EducationCalculatorResponse, summary="Education Calculator")
async def calculate_education(request: EducationCalculatorRequest):
    """
    Plan education funding for multiple children with multiple goals.
    
    **Features:**
    - Multiple children support
    - Multiple goals per child (8th-10th, 11th-12th, UG, PG)
    - Education inflation (default 10%)
    - Accumulated savings consideration
    - Per-child and global summaries
    - Product-wise return rates
    """
    try:
        return calculator_service.calculate_education(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 5. WEDDING CALCULATOR
# =============================================================================

@router.post("/wedding", response_model=WeddingCalculatorResponse, summary="Wedding Calculator")
async def calculate_wedding(request: WeddingCalculatorRequest):
    """
    Plan wedding savings with pricing tiers.
    
    **Wedding Types:**
    - Intimate, Simple, Traditional, Destination, Grand
    
    **Package Tiers:**
    - Standard, Premium, Diamond
    
    **Features:**
    - Pre-defined pricing table
    - Custom cost option
    - Inflation adjustment
    - Accumulated savings
    - Gap loan calculation
    """
    try:
        return calculator_service.calculate_wedding(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 6. GOLD CALCULATOR
# =============================================================================

    
@router.post("/gold", response_model=GoldCalculatorResponse, summary="Gold Calculator")
async def calculate_gold(request: GoldCalculatorRequest):
    """
    Plan gold purchase with purity-adjusted pricing.
    
    **Features:**
    - Gold purity: 24K, 22K, 18K, 14K, 13K
    - Purpose: Jewellery, Coins, Bars, Investment
    - Unit: Grams or KG
    - Price inflation (gold appreciation)
    - **Future target value** (inflation-adjusted)
    - **Projected corpus** (what investment will grow to)
    - Tax calculation per product
    """
    try:
        from app.services.gold_price_service import gold_price_service
        
        live_price = None
        
        if request.price_per_gram == 7500:  # Default = fetch live
            try:
                gold_prices = await gold_price_service.get_gold_prices()
                live_price = gold_price_service.get_price_for_purity(gold_prices, request.purity.value)
            except Exception as e:
                print(f"Failed to fetch live gold price: {e}")
        
        return await calculator_service.calculate_gold(request, live_price)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 7. RETIREMENT CALCULATOR
# =============================================================================

@router.post("/retirement", response_model=RetirementCalculatorResponse, summary="Retirement Calculator")
async def calculate_retirement(request: RetirementCalculatorRequest):
    """
    Comprehensive retirement planning calculator.
    
    **Inputs:**
    - Current age, retirement age, life expectancy
    - Current monthly expense
    - Current investments (8 product types)
    - Irregular cash flows (bonus, rental income)
    - Expected lumpsums (inheritance, property sale)
    - Assumptions (inflation, return rates)
    
    **Outputs:**
    - Expense at retirement (inflated)
    - Corpus needed (growing annuity)
    - Future value of current savings
    - Shortfall/Surplus
    - Normal, Step-up Amount, Step-up Percent options
    
    **Tax Treatment:**
    - LTCG for MF/Stocks
    - Slab rate for FD/RD/NCD
    - Exempt for PPF/EPF/NPS (simplified)
    """
    try:
        return calculator_service.calculate_retirement(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 8. SWP CALCULATOR
# =============================================================================

@router.post("/swp", response_model=SWPCalculatorResponse, summary="SWP Calculator")
async def calculate_swp(request: SWPCalculatorRequest):
    """
    Calculate Systematic Withdrawal Plan.
    
    **Features:**
    - Accumulation phase (optional years before withdrawal)
    - Withdrawal phase with monthly withdrawals
    - Step-up withdrawal option
    - Fund type: Equity or Debt
    - STCG/LTCG tax calculation
    - Yearly summary with tax breakdown
    - Month-by-month schedule
    
    **Tax Rules:**
    - Equity: STCG 20%, LTCG 12.5% (₹1.25L exemption)
    - Debt: Taxed as per slab (30% assumed)
    """
    try:
        return calculator_service.calculate_swp(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 9. PREPAYMENT CALCULATOR
# =============================================================================

@router.post("/prepayment", response_model=PrepaymentCalculatorResponse, summary="Loan Prepayment Calculator")
async def calculate_prepayment(request: PrepaymentCalculatorRequest):
    """
    Calculate loan prepayment scenarios.
    
    **Loan Types:**
    - Home, Car, Personal, Education, Business, Gold, Two-Wheeler
    
    **Scenarios:**
    1. **Original**: No prepayment baseline
    2. **Reduced Tenure**: Same EMI, fewer months
    3. **Reduced EMI**: Same tenure, lower EMI
    4. **Accelerated**: Extra EMIs per year (1-4)
    
    **Outputs:**
    - Interest saved
    - Months saved
    - EMI schedule
    - Recommendation (best option)
    """
    try:
        return calculator_service.calculate_prepayment(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 10. CASH SURPLUS CALCULATOR
# =============================================================================

@router.post("/cash-surplus", response_model=CashSurplusCalculatorResponse, summary="Cash Surplus Calculator")
async def calculate_cash_surplus(request: CashSurplusCalculatorRequest):
    """
    Analyze monthly/yearly cash flow and calculate surplus/shortfall.
    
    **Categories:**
    - Income: Salary, Rent, Dividend, Interest
    - Insurance: Life, Health, Motor, Other
    - Savings: MF, Stocks, FD, RD, NCD, Gold, PPF, NPS, etc.
    - Loans: Home, Personal, Vehicle, Education, Consumer (EMI + Pending)
    - Expenses: Household, Ration, Medicine, Transport, Entertainment, Education
    
    **Outputs:**
    - Total income (yearly/monthly)
    - Total expenses breakdown
    - Cash surplus/shortfall
    - Portfolio value
    
    **Note:** This is a pure cash-flow analyzer with no tax calculations.
    """
    try:
        return calculator_service.calculate_cash_surplus(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/products", summary="Get Investment Products")
async def get_investment_products():
    """Get all available investment products with default returns."""
    from app.constants.calculator_constants import INVESTMENT_PRODUCTS
    return {
        "products": [
            {
                "code": code.value,
                "name": info["name"],
                "default_return": info["default_return"],
                "risk_level": info["risk_level"].value,
                "supports_monthly": info["supports_monthly"],
                "supports_lumpsum": info["supports_lumpsum"],
                "tax_type": info["tax_type"].value,
            }
            for code, info in INVESTMENT_PRODUCTS.items()
        ]
    }


@router.get("/destinations", summary="Get Vacation Destinations")
async def get_vacation_destinations():
    """Get all vacation destinations with base prices."""
    from app.constants.calculator_constants import VACATION_DESTINATIONS
    return {
        "destinations": [
            {
                "id": dest_id,
                "name": info["name"],
                "base_price": info["base_price"],
                "type": info["type"].value,
            }
            for dest_id, info in VACATION_DESTINATIONS.items()
        ]
    }


@router.get("/wedding-pricing", summary="Get Wedding Pricing")
async def get_wedding_pricing():
    """Get wedding pricing table."""
    from app.constants.calculator_constants import WEDDING_PRICING, WeddingType, PackageTier
    return {
        "pricing": {
            wedding_type.value: {
                tier.value: price
                for tier, price in tiers.items()
            }
            for wedding_type, tiers in WEDDING_PRICING.items()
        }
    }


@router.get("/loan-types", summary="Get Loan Types")
async def get_loan_types():
    """Get loan types with default rates."""
    from app.constants.calculator_constants import LOAN_DEFAULTS
    return {
        "loan_types": [
            {
                "type": loan_type.value,
                "name": info["name"],
                "icon": info["icon"],
                "default_rate": info["default_rate"],
                "max_tenure_months": info["max_tenure_months"],
            }
            for loan_type, info in LOAN_DEFAULTS.items()
        ]
    }


@router.get("/banks", summary="Get Indian Banks")
async def get_indian_banks():
    """Get list of Indian banks."""
    from app.constants.calculator_constants import INDIAN_BANKS
    return {"banks": INDIAN_BANKS}



@router.get("/gold-price", summary="Get Live Gold Price")
async def get_live_gold_price(force_refresh: bool = False):
    """Get current gold prices (all purities)."""
    try:
        from app.services.gold_price_service import gold_price_service
        
        prices = await gold_price_service.get_gold_prices(force_refresh=force_refresh)
        return {
            "prices": {
                "24k": prices.price_gram_24k,
                "22k": prices.price_gram_22k,
                "21k": prices.price_gram_21k,
                "20k": prices.price_gram_20k,
                "18k": prices.price_gram_18k,
                "14k": prices.price_gram_14k,
                "10k": prices.price_gram_10k,
            },
            "market": {
                "open": prices.open_price,
                "high": prices.high_price,
                "low": prices.low_price,
                "prev_close": prices.prev_close_price,
                "change_percent": prices.change_percent,
            },
            "meta": {
                "source": prices.source,
                "is_cached": prices.is_cached,
                "cache_age_hours": prices.cache_age_hours,
                "fetched_at": prices.fetched_at.isoformat() if prices.fetched_at else None,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
