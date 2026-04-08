"""
Calculator Utilities
All mathematical formulas and helper functions for 10 calculators.
"""

import math
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP

from app.constants.calculator_constants import (
    EQUITY_LTCG_RATE,
    EQUITY_LTCG_EXEMPTION,
    EQUITY_STCG_RATE,
    EQUITY_HOLDING_THRESHOLD_MONTHS,
    TAX_SLABS_OLD,
    SAVINGS_80TTA_EXEMPTION,
    INVESTMENT_PRODUCTS,
    GOLD_PURITY_PERCENTAGE,
    WEDDING_PRICING,
    VACATION_DESTINATIONS,
    VACATION_PACKAGE_MULTIPLIERS,
    VACATION_PRICE_BREAKDOWN,
    LOAN_DEFAULTS,
    BINARY_SEARCH_ITERATIONS,
    BINARY_SEARCH_TOLERANCE,
    LOAN_BALANCE_PRECISION,
    AMORTIZATION_MAX_MONTHS,
    STEP_UP_YEARLY_DISCOUNT_RUPEE,
    STEP_UP_YEARLY_DISCOUNT_PERCENT,
    CALCULATION_PRECISION,
    ProductCode,
    TaxType,
    FundType,
    LoanType,
    GoldPurity,
    WeddingType,
    PackageTier,
    VacationPackageType,
    InvestmentFrequency,
)


# =============================================================================
# ROUNDING & FORMATTING UTILITIES
# =============================================================================

def round_currency(amount: float, precision: int = CALCULATION_PRECISION) -> float:
    """Round to currency precision (2 decimal places)"""
    if math.isnan(amount) or math.isinf(amount):
        return 0.0
    return round(amount, precision)


def round_to_nearest(amount: float, nearest: int = 100) -> float:
    """Round to nearest X (e.g., nearest 100)"""
    return round(amount / nearest) * nearest


def format_indian_currency(amount: float) -> str:
    """Format amount in Indian currency notation (L/Cr)"""
    abs_amount = abs(amount)
    sign = "-" if amount < 0 else ""
    
    if abs_amount >= 10000000:  # 1 Crore
        return f"{sign}₹{abs_amount / 10000000:.2f} Cr"
    elif abs_amount >= 100000:  # 1 Lakh
        return f"{sign}₹{abs_amount / 100000:.2f} L"
    else:
        return f"{sign}₹{abs_amount:,.0f}"


def format_indian_number(amount: float) -> str:
    """Format number with Indian comma separators"""
    if amount < 0:
        return f"-{format_indian_number(abs(amount))}"
    
    amount = int(round(amount))
    s = str(amount)
    
    if len(s) <= 3:
        return s
    
    # Last 3 digits
    result = s[-3:]
    s = s[:-3]
    
    # Add commas every 2 digits
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]
    
    return result.lstrip(",")


# =============================================================================
# CORE FINANCIAL FORMULAS
# =============================================================================

def calculate_future_value(principal: float, rate: float, years: float) -> float:
    """
    Calculate Future Value with compound interest.
    FV = P × (1 + r)^n
    
    Args:
        principal: Initial amount
        rate: Annual interest rate (percentage, e.g., 12 for 12%)
        years: Number of years
    """
    if years <= 0 or rate < 0:
        return principal
    return principal * math.pow(1 + rate / 100, years)


def calculate_present_value(future_value: float, rate: float, years: float) -> float:
    """
    Calculate Present Value (discount a future amount).
    PV = FV / (1 + r)^n
    """
    if years <= 0 or rate < 0:
        return future_value
    return future_value / math.pow(1 + rate / 100, years)


def calculate_sip_future_value(monthly_amount: float, annual_rate: float, years: float) -> float:
    """
    Calculate Future Value of SIP (Annuity Due - payment at beginning).
    FV = P × [(1 + r)^n - 1] / r × (1 + r)
    
    Args:
        monthly_amount: Monthly SIP amount
        annual_rate: Annual interest rate (percentage)
        years: Number of years
    """
    if years <= 0 or monthly_amount <= 0:
        return 0
    
    monthly_rate = annual_rate / 100 / 12
    months = int(years * 12)
    
    if monthly_rate == 0:
        return monthly_amount * months
    
    factor = math.pow(1 + monthly_rate, months)
    return monthly_amount * ((factor - 1) / monthly_rate) * (1 + monthly_rate)


def calculate_required_monthly_sip(target_amount: float, annual_rate: float, years: float) -> float:
    """
    Calculate required monthly SIP for a target (reverse SIP).
    P = FV / [((1 + r)^n - 1) / r × (1 + r)]
    """
    if years <= 0 or target_amount <= 0:
        return 0
    
    monthly_rate = annual_rate / 100 / 12
    months = int(years * 12)
    
    if monthly_rate == 0:
        return target_amount / months
    
    factor = math.pow(1 + monthly_rate, months)
    return target_amount / (((factor - 1) / monthly_rate) * (1 + monthly_rate))


def calculate_yearly_investment(target_amount: float, annual_rate: float, years: float) -> float:
    """
    Calculate required yearly investment for a target (Annuity Due).
    """
    if years <= 0 or target_amount <= 0:
        return 0
    
    rate = annual_rate / 100
    
    if rate == 0:
        return target_amount / years
    
    factor = math.pow(1 + rate, years)
    return target_amount / (((factor - 1) / rate) * (1 + rate))


def calculate_lumpsum_required(target_amount: float, annual_rate: float, years: float) -> float:
    """
    Calculate required one-time investment for a target (Present Value).
    """
    return calculate_present_value(target_amount, annual_rate, years)


# =============================================================================
# STEP-UP SIP FORMULAS
# =============================================================================

def calculate_step_up_sip_fv_amount(
    starting_monthly: float,
    annual_step_up: float,  # ₹ per year
    annual_rate: float,
    years: float
) -> float:
    """
    Calculate FV of SIP with annual rupee increment.
    """
    if years <= 0 or starting_monthly <= 0:
        return 0
    
    total_fv = 0
    current_monthly = starting_monthly
    years_int = int(years)
    
    for year in range(years_int):
        years_remaining = years - year
        # FV of this year's SIP compounded to end
        yearly_fv = calculate_sip_future_value(current_monthly, annual_rate, 1)
        total_fv += calculate_future_value(yearly_fv, annual_rate, years_remaining - 1)
        # Increase for next year
        current_monthly += annual_step_up / 12
    
    return total_fv


def calculate_step_up_sip_fv_percent(
    starting_monthly: float,
    annual_step_up_percent: float,  # % per year
    annual_rate: float,
    years: float
) -> float:
    """
    Calculate FV of SIP with annual percentage increment.
    """
    if years <= 0 or starting_monthly <= 0:
        return 0
    
    total_fv = 0
    current_monthly = starting_monthly
    years_int = int(years)
    
    for year in range(years_int):
        years_remaining = years - year
        yearly_fv = calculate_sip_future_value(current_monthly, annual_rate, 1)
        total_fv += calculate_future_value(yearly_fv, annual_rate, years_remaining - 1)
        current_monthly *= (1 + annual_step_up_percent / 100)
    
    return total_fv


def calculate_required_step_up_sip_amount(
    target_amount: float,
    annual_step_up: float,  # ₹ per year
    annual_rate: float,
    years: float
) -> float:
    """
    Calculate required starting monthly SIP with annual ₹ step-up (binary search).
    """
    if years <= 0 or target_amount <= 0:
        return 0
    
    low, high = 0, target_amount
    result = 0
    
    for _ in range(BINARY_SEARCH_ITERATIONS):
        mid = (low + high) / 2
        fv = calculate_step_up_sip_fv_amount(mid, annual_step_up, annual_rate, years)
        
        if abs(fv - target_amount) < BINARY_SEARCH_TOLERANCE:
            result = mid
            break
        
        if fv < target_amount:
            low = mid
        else:
            high = mid
        result = mid
    
    return result


def calculate_required_step_up_sip_percent(
    target_amount: float,
    annual_step_up_percent: float,  # % per year
    annual_rate: float,
    years: float
) -> float:
    """
    Calculate required starting monthly SIP with annual % step-up (binary search).
    """
    if years <= 0 or target_amount <= 0:
        return 0
    
    low, high = 0, target_amount
    result = 0
    
    for _ in range(BINARY_SEARCH_ITERATIONS):
        mid = (low + high) / 2
        fv = calculate_step_up_sip_fv_percent(mid, annual_step_up_percent, annual_rate, years)
        
        if abs(fv - target_amount) < BINARY_SEARCH_TOLERANCE:
            result = mid
            break
        
        if fv < target_amount:
            low = mid
        else:
            high = mid
        result = mid
    
    return result


# =============================================================================
# EMI & LOAN FORMULAS
# =============================================================================

def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """
    Calculate Equated Monthly Installment.
    EMI = P × r × (1 + r)^n / [(1 + r)^n - 1]
    """
    if principal <= 0 or tenure_months <= 0:
        return 0
    if annual_rate <= 0:
        return principal / tenure_months
    
    monthly_rate = annual_rate / 12 / 100
    factor = math.pow(1 + monthly_rate, tenure_months)
    return (principal * monthly_rate * factor) / (factor - 1)


def generate_amortization_schedule(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    start_date: date,
    emi: Optional[float] = None,
    prepayments: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Generate month-by-month amortization schedule.
    """
    if emi is None:
        emi = calculate_emi(principal, annual_rate, tenure_months)
    
    prepayments = prepayments or []
    monthly_rate = annual_rate / 12 / 100
    balance = principal
    schedule = []
    
    # Sort prepayments by date
    sorted_prepayments = sorted(prepayments, key=lambda x: x.get("date", date.max))
    
    for month in range(1, min(tenure_months + 1, AMORTIZATION_MAX_MONTHS)):
        if balance <= LOAN_BALANCE_PRECISION:
            break
        
        current_date = add_months(start_date, month - 1)
        opening_balance = balance
        
        interest_component = balance * monthly_rate
        principal_component = min(emi - interest_component, balance)
        actual_emi = interest_component + principal_component
        
        # Check for prepayments this month
        prepayment_amount = 0
        for pp in sorted_prepayments:
            pp_date = pp.get("date")
            if pp_date and months_between(start_date, pp_date) + 1 == month:
                prepayment_amount += pp.get("amount", 0)
        
        # Cap prepayment at remaining balance
        prepayment_amount = min(prepayment_amount, balance - principal_component)
        
        closing_balance = max(0, balance - principal_component - prepayment_amount)
        
        schedule.append({
            "month": month,
            "date": current_date,
            "opening_balance": round_currency(opening_balance),
            "emi": round_currency(actual_emi),
            "principal": round_currency(principal_component),
            "interest": round_currency(interest_component),
            "prepayment": round_currency(prepayment_amount),
            "closing_balance": round_currency(closing_balance),
        })
        
        balance = closing_balance
    
    return schedule


def calculate_new_tenure(
    outstanding_principal: float,
    annual_rate: float,
    emi: float
) -> int:
    """
    Calculate remaining months after prepayment keeping same EMI.
    n = ln(EMI / (EMI - P×r)) / ln(1+r)
    """
    if outstanding_principal <= 0:
        return 0
    if annual_rate <= 0:
        return math.ceil(outstanding_principal / emi)
    
    monthly_rate = annual_rate / 12 / 100
    denominator = emi - outstanding_principal * monthly_rate
    
    if denominator <= 0:
        return 9999  # EMI too low to cover interest
    
    return math.ceil(math.log(emi / denominator) / math.log(1 + monthly_rate))


def generate_accelerated_schedule(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    start_date: date,
    emi: float,
    extra_emis_per_year: int,
    prepayments: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Generate amortization with extra EMIs distributed across the year.
    """
    prepayments = prepayments or []
    monthly_rate = annual_rate / 12 / 100
    balance = principal
    schedule = []
    
    # Calculate which months get extra EMI
    extra_emi_months = []
    if extra_emis_per_year > 0:
        interval = 12 // extra_emis_per_year
        for i in range(extra_emis_per_year):
            extra_emi_months.append((i + 1) * interval)
    
    sorted_prepayments = sorted(prepayments, key=lambda x: x.get("date", date.max))
    
    month = 0
    while balance > LOAN_BALANCE_PRECISION and month < tenure_months * 2:
        month += 1
        current_date = add_months(start_date, month - 1)
        opening_balance = balance
        
        interest_component = balance * monthly_rate
        principal_component = min(emi - interest_component, balance)
        actual_emi = interest_component + principal_component
        
        # Check for prepayments
        prepayment_amount = 0
        for pp in sorted_prepayments:
            pp_date = pp.get("date")
            if pp_date and months_between(start_date, pp_date) + 1 == month:
                prepayment_amount += pp.get("amount", 0)
        
        # Check for extra EMI this month
        year_month = ((month - 1) % 12) + 1
        if year_month in extra_emi_months:
            prepayment_amount += emi
        
        prepayment_amount = min(prepayment_amount, balance - principal_component)
        closing_balance = max(0, balance - principal_component - prepayment_amount)
        
        schedule.append({
            "month": month,
            "date": current_date,
            "opening_balance": round_currency(opening_balance),
            "emi": round_currency(actual_emi),
            "principal": round_currency(principal_component),
            "interest": round_currency(interest_component),
            "prepayment": round_currency(prepayment_amount),
            "closing_balance": round_currency(closing_balance),
        })
        
        balance = closing_balance
        if balance <= LOAN_BALANCE_PRECISION:
            break
    
    return schedule


# =============================================================================
# TAX CALCULATION FORMULAS
# =============================================================================

def calculate_equity_tax(gains: float, holding_period: str = "long") -> Dict[str, float]:
    """
    Calculate tax on equity gains (MF, Stocks, ELSS).
    
    Args:
        gains: Capital gains amount
        holding_period: 'long' (>12 months) or 'short' (<=12 months)
    
    Returns:
        Dict with stcg_tax, ltcg_tax, ltcg_exemption, total_tax
    """
    if gains <= 0:
        return {
            "short_term_gains": 0,
            "long_term_gains": 0,
            "stcg_tax": 0,
            "ltcg_tax": 0,
            "ltcg_exemption": 0,
            "total_tax": 0
        }
    
    if holding_period == "long":
        exemption = min(EQUITY_LTCG_EXEMPTION, gains)
        taxable_gains = max(0, gains - EQUITY_LTCG_EXEMPTION)
        ltcg_tax = taxable_gains * EQUITY_LTCG_RATE
        return {
            "short_term_gains": 0,
            "long_term_gains": gains,
            "stcg_tax": 0,
            "ltcg_tax": round_currency(ltcg_tax),
            "ltcg_exemption": round_currency(exemption),
            "total_tax": round_currency(ltcg_tax)
        }
    else:
        stcg_tax = gains * EQUITY_STCG_RATE
        return {
            "short_term_gains": gains,
            "long_term_gains": 0,
            "stcg_tax": round_currency(stcg_tax),
            "ltcg_tax": 0,
            "ltcg_exemption": 0,
            "total_tax": round_currency(stcg_tax)
        }


def calculate_interest_tax(interest: float, apply_80tta: bool = False) -> float:
    """
    Calculate tax on interest income using old regime slabs.
    """
    if interest <= 0:
        return 0
    
    # Apply 80TTA exemption for savings interest
    taxable_interest = interest
    if apply_80tta:
        taxable_interest = max(0, interest - SAVINGS_80TTA_EXEMPTION)
    
    if taxable_interest <= 0:
        return 0
    
    tax = 0
    remaining = taxable_interest
    
    for slab in TAX_SLABS_OLD:
        if remaining <= 0:
            break
        slab_amount = min(remaining, slab["max"] - slab["min"] + 1)
        tax += slab_amount * (slab["rate"] / 100)
        remaining -= slab_amount
    
    return round_currency(tax)


def calculate_post_tax_value(
    principal: float,
    future_value: float,
    product_code: ProductCode,
    years: float = 1
) -> Dict[str, float]:
    """
    Calculate post-tax value based on product type.
    """
    gains = future_value - principal
    
    product_info = INVESTMENT_PRODUCTS.get(product_code, {})
    tax_type = product_info.get("tax_type", TaxType.SLAB)
    
    if tax_type == TaxType.EXEMPT:
        return {
            "pre_tax_value": round_currency(future_value),
            "gains": round_currency(gains),
            "tax": 0,
            "post_tax_value": round_currency(future_value),
            "tax_type": "Exempt"
        }
    
    elif tax_type == TaxType.LTCG:
        holding = "long" if years >= 1 else "short"
        tax_result = calculate_equity_tax(gains, holding)
        return {
            "pre_tax_value": round_currency(future_value),
            "gains": round_currency(gains),
            "tax": tax_result["total_tax"],
            "post_tax_value": round_currency(future_value - tax_result["total_tax"]),
            "tax_type": "LTCG (12.5%)" if holding == "long" else "STCG (20%)"
        }
    
    else:  # SLAB
        apply_80tta = product_code == ProductCode.SAVINGS
        tax = calculate_interest_tax(gains, apply_80tta)
        return {
            "pre_tax_value": round_currency(future_value),
            "gains": round_currency(gains),
            "tax": tax,
            "post_tax_value": round_currency(future_value - tax),
            "tax_type": "Slab Rate"
        }


# =============================================================================
# PRODUCT & RETURN UTILITIES
# =============================================================================

def calculate_weighted_return(products: List[Dict[str, Any]]) -> float:
    """
    Calculate weighted average return from product selection.
    """
    if not products:
        return 12.0  # Default fallback
    
    total_allocation = sum(p.get("allocation", 0) for p in products)
    if total_allocation <= 0:
        return 12.0
    
    weighted_return = 0
    for p in products:
        allocation = p.get("allocation", 0)
        return_rate = p.get("return_rate") or p.get("effective_return_rate")
        
        if return_rate is None:
            product_code = p.get("product_code")
            product_info = INVESTMENT_PRODUCTS.get(product_code, {})
            return_rate = product_info.get("default_return", 12.0)
        
        weighted_return += (allocation * return_rate) / total_allocation
    
    return round(weighted_return, 2)


def check_supports_monthly(products: List[Dict[str, Any]]) -> bool:
    """
    Check if any selected product supports monthly SIP.
    """
    for p in products:
        product_code = p.get("product_code")
        product_info = INVESTMENT_PRODUCTS.get(product_code, {})
        if product_info.get("supports_monthly", False) and p.get("allocation", 0) > 0:
            return True
    return False


def check_supports_lumpsum(products: List[Dict[str, Any]]) -> bool:
    """
    Check if any selected product supports lumpsum.
    """
    for p in products:
        product_code = p.get("product_code")
        product_info = INVESTMENT_PRODUCTS.get(product_code, {})
        if product_info.get("supports_lumpsum", True) and p.get("allocation", 0) > 0:
            return True
    return False


# =============================================================================
# RETIREMENT SPECIFIC FORMULAS
# =============================================================================

def calculate_retirement_corpus(
    monthly_expense_at_retirement: float,
    post_retirement_inflation: float,
    return_on_kitty: float,
    retirement_years: int
) -> float:
    """
    Calculate corpus needed using present value of growing annuity.
    """
    if retirement_years <= 0 or monthly_expense_at_retirement <= 0:
        return 0
    
    annual_expense = monthly_expense_at_retirement * 12
    real_rate = (return_on_kitty - post_retirement_inflation) / 100
    
    if abs(real_rate) < 0.0001:
        return annual_expense * retirement_years
    
    inflation_factor = 1 + post_retirement_inflation / 100
    return_factor = 1 + return_on_kitty / 100
    
    corpus = annual_expense * (
        (1 - math.pow(inflation_factor / return_factor, retirement_years)) / real_rate
    )
    
    return max(0, corpus)


# =============================================================================
# SWP SPECIFIC FORMULAS
# =============================================================================

def calculate_swp_accumulation(principal: float, annual_return: float, years: int) -> float:
    """
    Calculate corpus value after accumulation phase.
    """
    if years <= 0:
        return principal
    return calculate_future_value(principal, annual_return, years)


def get_withdrawal_for_month(
    month: int,
    base_withdrawal: float,
    annual_increase: float
) -> float:
    """
    Calculate withdrawal amount for a given month with annual step-up.
    """
    year_number = (month - 1) // 12
    multiplier = math.pow(1 + annual_increase / 100, year_number)
    return base_withdrawal * multiplier


def calculate_swp_schedule(
    principal: float,
    monthly_withdrawal: float,
    accumulation_years: int,
    withdrawal_years: int,
    annual_return: float,
    fund_type: str,
    annual_withdrawal_increase: float = 0
) -> Dict[str, Any]:
    """
    Calculate complete SWP schedule with tax.
    """
    # Accumulation phase
    value_at_swp_start = calculate_swp_accumulation(principal, annual_return, accumulation_years)
    
    monthly_rate = annual_return / 100 / 12
    months = withdrawal_years * 12
    months_already_held = accumulation_years * 12
    
    balance = value_at_swp_start
    total_investment = principal
    total_withdrawn = 0
    total_principal_returned = 0
    
    short_term_gains = 0
    long_term_gains = 0
    
    withdrawal_breakdown = []
    
    for month in range(1, months + 1):
        if balance <= 0:
            break
        
        opening_balance = balance
        
        # Apply monthly growth
        balance = balance * (1 + monthly_rate)
        
        # Calculate gain ratio
        total_gains_in_balance = balance - total_investment + total_principal_returned
        gain_ratio = max(0, min(1, total_gains_in_balance / balance)) if balance > 0 else 0
        
        # Get withdrawal amount
        withdrawal_amount = get_withdrawal_for_month(month, monthly_withdrawal, annual_withdrawal_increase)
        actual_withdrawal = min(withdrawal_amount, balance)
        
        # Split into capital gain and principal
        capital_gain_in_withdrawal = actual_withdrawal * gain_ratio
        principal_in_withdrawal = actual_withdrawal - capital_gain_in_withdrawal
        
        # Determine short-term vs long-term
        total_months_from_investment = months_already_held + month
        is_short_term = total_months_from_investment <= EQUITY_HOLDING_THRESHOLD_MONTHS
        
        if fund_type == FundType.EQUITY or fund_type == "equity":
            if is_short_term:
                short_term_gains += capital_gain_in_withdrawal
            else:
                long_term_gains += capital_gain_in_withdrawal
        else:
            short_term_gains += capital_gain_in_withdrawal  # All taxed as slab for debt
        
        balance -= actual_withdrawal
        total_withdrawn += actual_withdrawal
        total_principal_returned += principal_in_withdrawal
        
        withdrawal_breakdown.append({
            "month": month,
            "year": (month - 1) // 12 + 1,
            "opening_balance": round_currency(opening_balance),
            "withdrawal": round_currency(actual_withdrawal),
            "capital_gain_in_withdrawal": round_currency(capital_gain_in_withdrawal),
            "principal_in_withdrawal": round_currency(principal_in_withdrawal),
            "closing_balance": round_currency(balance),
            "is_short_term": is_short_term
        })
    
    # Calculate tax
    if fund_type == FundType.EQUITY or fund_type == "equity":
        stcg_tax = short_term_gains * EQUITY_STCG_RATE
        ltcg_exemption = min(EQUITY_LTCG_EXEMPTION, long_term_gains)
        taxable_ltcg = max(0, long_term_gains - EQUITY_LTCG_EXEMPTION)
        ltcg_tax = taxable_ltcg * EQUITY_LTCG_RATE
    else:
        stcg_tax = (short_term_gains + long_term_gains) * 0.30  # Assumed 30% slab
        ltcg_tax = 0
        ltcg_exemption = 0
    
    total_tax = stcg_tax + ltcg_tax
    total_gain = total_withdrawn + balance - principal
    net_after_tax = total_withdrawn + balance - total_tax
    
    total_gains = short_term_gains + long_term_gains
    effective_tax_rate = (total_tax / total_gains * 100) if total_gains > 0 else 0
    
    return {
        "value_at_swp_start": round_currency(value_at_swp_start),
        "total_growth_during_accumulation": round_currency(value_at_swp_start - principal),
        "total_withdrawals": round_currency(total_withdrawn),
        "number_of_withdrawals": len(withdrawal_breakdown),
        "final_balance": round_currency(balance),
        "total_gain": round_currency(total_gain),
        "tax_breakdown": {
            "total_gains": round_currency(total_gains),
            "short_term_gains": round_currency(short_term_gains),
            "long_term_gains": round_currency(long_term_gains),
            "stcg_tax": round_currency(stcg_tax),
            "ltcg_tax": round_currency(ltcg_tax),
            "ltcg_exemption": round_currency(ltcg_exemption),
            "total_tax": round_currency(total_tax),
            "effective_tax_rate": round(effective_tax_rate, 2)
        },
        "net_amount_after_tax": round_currency(net_after_tax),
        "withdrawal_breakdown": withdrawal_breakdown
    }


# =============================================================================
# GOLD SPECIFIC UTILITIES
# =============================================================================

def get_gold_purity_percentage(purity: GoldPurity) -> float:
    """Get purity percentage for gold karat."""
    return GOLD_PURITY_PERCENTAGE.get(purity, 0.999)


def calculate_gold_price_for_purity(price_24k: float, purity: GoldPurity) -> float:
    """Calculate gold price per gram for specific purity."""
    purity_percent = get_gold_purity_percentage(purity)
    return price_24k * purity_percent


def calculate_gold_target_value(
    quantity: float,
    unit: str,
    price_per_gram: float,
    purity: GoldPurity
) -> float:
    """Calculate total gold target value."""
    quantity_grams = quantity * 1000 if unit == "kg" else quantity
    adjusted_price = calculate_gold_price_for_purity(price_per_gram, purity)
    return quantity_grams * adjusted_price


# =============================================================================
# WEDDING SPECIFIC UTILITIES
# =============================================================================

def get_wedding_cost(wedding_type: WeddingType, package_tier: PackageTier) -> float:
    """Get wedding cost from pricing table."""
    wedding_prices = WEDDING_PRICING.get(wedding_type, {})
    return wedding_prices.get(package_tier, 2000000)  # Default 20L


# =============================================================================
# VACATION SPECIFIC UTILITIES
# =============================================================================

def get_vacation_cost(
    destination_id: str,
    package_type: VacationPackageType,
    travelers: int
) -> Tuple[float, Dict[str, float]]:
    """
    Get vacation cost with breakdown.
    Returns (total_cost, price_breakdown)
    """
    destination = VACATION_DESTINATIONS.get(destination_id)
    if not destination:
        return 0, {}
    
    base_price = destination["base_price"]
    multiplier = VACATION_PACKAGE_MULTIPLIERS.get(package_type, 1.0)
    price_per_person = base_price * multiplier
    total_cost = price_per_person * travelers
    
    # Calculate breakdown
    breakdown = {}
    for component, percent in VACATION_PRICE_BREAKDOWN.items():
        breakdown[component] = round_currency(total_cost * percent)
    
    return total_cost, breakdown


# =============================================================================
# DATE UTILITIES
# =============================================================================

def add_months(start_date: date, months: int) -> date:
    """Add months to a date."""
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, [31, 29 if year % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


def months_between(start_date: date, end_date: date) -> int:
    """Calculate months between two dates."""
    return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)


# =============================================================================
# CASH FLOW UTILITIES
# =============================================================================

def to_yearly(amount: float, frequency: str) -> float:
    """Convert amount to yearly based on frequency."""
    multipliers = {
        "monthly": 12,
        "quarterly": 4,
        "half_yearly": 2,
        "yearly": 1,
        "one_time": 1
    }
    return amount * multipliers.get(frequency, 1)


def to_monthly(amount: float, frequency: str) -> float:
    """Convert amount to monthly based on frequency."""
    divisors = {
        "monthly": 1,
        "quarterly": 3,
        "half_yearly": 6,
        "yearly": 12,
        "one_time": 12
    }
    return amount / divisors.get(frequency, 1)


# =============================================================================
# INVESTMENT-BASED MODE UTILITIES
# =============================================================================

def calculate_projected_corpus(
    investment_amount: float,
    frequency: str,
    annual_return: float,
    years: float
) -> float:
    """
    Calculate projected corpus for investment-based mode.
    """
    if frequency == "monthly":
        return calculate_sip_future_value(investment_amount, annual_return, years)
    elif frequency == "yearly":
        # Yearly investment as annuity due
        rate = annual_return / 100
        if rate == 0:
            return investment_amount * years
        factor = math.pow(1 + rate, years)
        return investment_amount * ((factor - 1) / rate) * (1 + rate)
    else:  # one_time / lumpsum
        return calculate_future_value(investment_amount, annual_return, years)


def calculate_gap_loan(
    gap_amount: float,
    interest_rate: float,
    tenure_months: int
) -> Dict[str, float]:
    """
    Calculate loan details for gap financing.
    """
    if gap_amount <= 0:
        return {
            "loan_amount": 0,
            "interest_rate": interest_rate,
            "tenure_months": tenure_months,
            "emi": 0,
            "total_interest": 0,
            "total_payment": 0
        }
    
    emi = calculate_emi(gap_amount, interest_rate, tenure_months)
    total_payment = emi * tenure_months
    total_interest = total_payment - gap_amount
    
    return {
        "loan_amount": round_currency(gap_amount),
        "interest_rate": interest_rate,
        "tenure_months": tenure_months,
        "emi": round_currency(emi),
        "total_interest": round_currency(total_interest),
        "total_payment": round_currency(total_payment)
    }