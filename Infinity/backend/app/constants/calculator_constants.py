"""
Calculator Constants
All rates, products, pricing tables, and configuration for 10 calculators.
Aligned with database enums and Lovable frontend specs.
"""

from enum import Enum
from typing import Dict, List, Any
from decimal import Decimal

# =============================================================================
# ENUMS (Matching DB where applicable, new ones for calculators)
# =============================================================================

class CalculatorType(str, Enum):
    """All calculator types - maps to calculator_results.calculator_type"""
    SIP_LUMPSUM_GOAL = "sip_lumpsum_goal"  # Unified calculator
    VEHICLE = "vehicle"
    VACATION = "vacation"
    EDUCATION = "education"
    WEDDING = "wedding"
    GOLD = "gold"
    RETIREMENT = "retirement"
    SWP = "swp"
    PREPAYMENT = "prepayment"
    CASH_SURPLUS = "cash_surplus"


class SIPMode(str, Enum):
    """Mode for unified SIP/Lumpsum/Goal calculator"""
    SIP = "sip"                    # Calculate corpus from SIP
    LUMPSUM = "lumpsum"            # Calculate corpus from lumpsum
    GOAL_SIP = "goal_sip"          # Calculate required SIP for goal
    GOAL_LUMPSUM = "goal_lumpsum"  # Calculate required lumpsum for goal
    GOAL_BOTH = "goal_both"        # Show both SIP and lumpsum options


class CalculationMode(str, Enum):
    """Dual-mode calculation: target-based or investment-based"""
    TARGET_BASED = "target_based"        # "I need X" → calculate required SIP
    INVESTMENT_BASED = "investment_based" # "I can invest X" → calculate corpus + gap loan


class InvestmentFrequency(str, Enum):
    """Investment frequency options - aligns with premium_frequency_type"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half_yearly"
    YEARLY = "yearly"
    ONE_TIME = "one_time"


class ProductCode(str, Enum):
    """Investment product codes - aligns with product_category_type"""
    MUTUAL_FUND = "mutual_fund"
    STOCKS = "stocks"
    FIXED_DEPOSIT = "fixed_deposit"
    RECURRING_DEPOSIT = "recurring_deposit"
    PPF = "ppf"
    EPF = "epf"
    NPS = "nps"
    BONDS = "bonds"
    NCD = "ncd"
    GOLD = "gold"
    GOLD_ETF = "gold_etf"
    SGB = "sgb"
    ELSS = "elss"
    SAVINGS = "savings"
    ULIP = "ulip"
    DEBT_MF = "debt_mf"
    HYBRID_MF = "hybrid_mf"
    REAL_ESTATE = "real_estate"


class TaxType(str, Enum):
    """Tax treatment categories"""
    LTCG = "ltcg"           # Long-term capital gains (MF, Stocks, ELSS)
    STCG = "stcg"           # Short-term capital gains
    SLAB = "slab"           # Taxed per income slab (FD, RD, NCD)
    EXEMPT = "exempt"       # Tax-free (PPF, SGB maturity, EPF)
    HYBRID = "hybrid"       # Mixed treatment


class RiskLevel(str, Enum):
    """Product risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Vehicle Enums - aligns with vehicle_type in DB
class VehicleType(str, Enum):
    """Vehicle types - matches DB vehicle_type"""
    CAR = "car"
    BIKE = "bike"


class VehicleCommercialType(str, Enum):
    """Commercial vehicle subtypes"""
    TRUCK = "truck"
    AUTO_RICKSHAW = "auto_rickshaw"
    TEMPO = "tempo"
    BUS = "bus"
    VAN = "van"
    OTHER_COMMERCIAL = "other_commercial"


# Gold Enums
class GoldPurity(str, Enum):
    """Gold karat/purity options"""
    K24 = "24"  # 99.9% pure
    K22 = "22"  # 91.6% pure
    K18 = "18"  # 75% pure
    K14 = "14"  # 58.3% pure
    K13 = "13"  # 54.2% pure


class GoldPurpose(str, Enum):
    """Purpose of gold purchase"""
    JEWELLERY = "jewellery"
    COINS = "coins"
    BARS = "bars"
    INVESTMENT = "investment"


class GoldUnit(str, Enum):
    """Gold quantity unit"""
    GRAMS = "grams"
    KG = "kg"


# Wedding Enums
class WeddingType(str, Enum):
    """Wedding scale/type"""
    INTIMATE = "intimate"
    SIMPLE = "simple"
    TRADITIONAL = "traditional"
    DESTINATION = "destination"
    GRAND = "grand"


class PackageTier(str, Enum):
    """Wedding package tier"""
    STANDARD = "standard"
    PREMIUM = "premium"
    DIAMOND = "diamond"


# Vacation Enums - aligns with lifestyle_subtype
class VacationType(str, Enum):
    """Vacation type - matches lifestyle_subtype"""
    DOMESTIC = "vacation_domestic"
    INTERNATIONAL = "vacation_international"


class VacationPackageType(str, Enum):
    """Vacation package tier"""
    STANDARD = "standard"
    PREMIUM = "premium"
    BUSINESS = "business"


# SWP Enums
class FundType(str, Enum):
    """Fund type for SWP tax calculation"""
    EQUITY = "equity"
    DEBT = "debt"


# Prepayment/Loan Enums
class LoanType(str, Enum):
    """Loan types for prepayment calculator"""
    HOME = "home"
    CAR = "car"
    PERSONAL = "personal"
    EDUCATION = "education"
    BUSINESS = "business"
    GOLD = "gold"
    TWO_WHEELER = "two_wheeler"
    OTHER = "other"


class PrepaymentStrategy(str, Enum):
    """Prepayment impact strategy"""
    REDUCE_TENURE = "reduce_tenure"
    REDUCE_EMI = "reduce_emi"


# Step-up Enums
class StepUpType(str, Enum):
    """Step-up type for SIP"""
    NONE = "none"
    AMOUNT = "amount"       # Fixed ₹ increase
    PERCENTAGE = "percentage"  # % increase


class StepUpFrequency(str, Enum):
    """Step-up frequency"""
    YEARLY = "yearly"
    BI_YEARLY = "bi_yearly"


# =============================================================================
# TAX CONSTANTS
# =============================================================================

# Equity Tax Rates (MF, Stocks, ELSS)
EQUITY_LTCG_RATE: float = 0.125  # 12.5%
EQUITY_LTCG_EXEMPTION: float = 125000  # ₹1.25 Lakh
EQUITY_STCG_RATE: float = 0.20  # 20%
EQUITY_HOLDING_THRESHOLD_MONTHS: int = 12  # >12 months = long-term

# Debt Tax Rates
DEBT_SLAB_RATE: float = 0.30  # Assumed 30% slab for debt instruments

# Old Tax Regime Slabs (for interest income)
TAX_SLABS_OLD: List[Dict[str, Any]] = [
    {"min": 0, "max": 250000, "rate": 0},
    {"min": 250001, "max": 500000, "rate": 5},
    {"min": 500001, "max": 1000000, "rate": 20},
    {"min": 1000001, "max": float("inf"), "rate": 30},
]

# Section 80TTA - Savings Interest Exemption
SAVINGS_80TTA_EXEMPTION: float = 10000  # ₹10,000

# =============================================================================
# INVESTMENT PRODUCTS CONFIGURATION
# =============================================================================

INVESTMENT_PRODUCTS: Dict[str, Dict[str, Any]] = {
    ProductCode.MUTUAL_FUND: {
        "name": "Mutual Funds",
        "code": "mutual_fund",
        "default_return": 12.0,
        "risk_level": RiskLevel.HIGH,
        "supports_monthly": True,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.LTCG,
        "min_investment": 500,
    },
    ProductCode.STOCKS: {
        "name": "Stocks",
        "code": "stocks",
        "default_return": 12.0,
        "risk_level": RiskLevel.HIGH,
        "supports_monthly": True,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.LTCG,
        "min_investment": 1000,
    },
    ProductCode.FIXED_DEPOSIT: {
        "name": "Fixed Deposit",
        "code": "fixed_deposit",
        "default_return": 7.0,
        "risk_level": RiskLevel.LOW,
        "supports_monthly": False,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.SLAB,
        "min_investment": 1000,
    },
    ProductCode.RECURRING_DEPOSIT: {
        "name": "Recurring Deposit",
        "code": "recurring_deposit",
        "default_return": 7.5,
        "risk_level": RiskLevel.LOW,
        "supports_monthly": True,
        "supports_yearly": True,
        "supports_lumpsum": False,
        "tax_type": TaxType.SLAB,
        "min_investment": 500,
    },
    ProductCode.NCD: {
        "name": "NCD / Bonds",
        "code": "ncd",
        "default_return": 9.0,
        "risk_level": RiskLevel.MEDIUM,
        "supports_monthly": False,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.SLAB,
        "min_investment": 10000,
    },
    ProductCode.PPF: {
        "name": "PPF",
        "code": "ppf",
        "default_return": 7.1,
        "risk_level": RiskLevel.LOW,
        "supports_monthly": True,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.EXEMPT,
        "min_investment": 500,
    },
    ProductCode.EPF: {
        "name": "Provident Fund",
        "code": "epf",
        "default_return": 8.1,
        "risk_level": RiskLevel.LOW,
        "supports_monthly": True,
        "supports_yearly": False,
        "supports_lumpsum": False,
        "tax_type": TaxType.EXEMPT,
        "min_investment": 0,
    },
    ProductCode.NPS: {
        "name": "NPS",
        "code": "nps",
        "default_return": 10.0,
        "risk_level": RiskLevel.MEDIUM,
        "supports_monthly": True,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.HYBRID,  # 60% exempt, 40% annuity taxed
        "min_investment": 500,
    },
    ProductCode.SAVINGS: {
        "name": "Savings Account",
        "code": "savings",
        "default_return": 4.0,
        "risk_level": RiskLevel.LOW,
        "supports_monthly": False,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.SLAB,
        "min_investment": 0,
    },
    ProductCode.GOLD: {
        "name": "Gold",
        "code": "gold",
        "default_return": 8.0,
        "risk_level": RiskLevel.MEDIUM,
        "supports_monthly": False,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.LTCG,
        "min_investment": 1000,
    },
    ProductCode.GOLD_ETF: {
        "name": "Gold ETF",
        "code": "gold_etf",
        "default_return": 8.0,
        "risk_level": RiskLevel.MEDIUM,
        "supports_monthly": False,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.LTCG,
        "min_investment": 1000,
    },
    ProductCode.SGB: {
        "name": "Sovereign Gold Bond",
        "code": "sgb",
        "default_return": 8.5,
        "risk_level": RiskLevel.LOW,
        "supports_monthly": False,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.EXEMPT,  # Exempt if held till maturity
        "min_investment": 5000,
    },
    ProductCode.ELSS: {
        "name": "ELSS",
        "code": "elss",
        "default_return": 12.0,
        "risk_level": RiskLevel.HIGH,
        "supports_monthly": True,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.LTCG,
        "min_investment": 500,
    },
    ProductCode.DEBT_MF: {
        "name": "Debt Mutual Fund",
        "code": "debt_mf",
        "default_return": 7.0,
        "risk_level": RiskLevel.LOW,
        "supports_monthly": True,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.SLAB,
        "min_investment": 500,
    },
    ProductCode.HYBRID_MF: {
        "name": "Hybrid Mutual Fund",
        "code": "hybrid_mf",
        "default_return": 10.0,
        "risk_level": RiskLevel.MEDIUM,
        "supports_monthly": True,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.LTCG,
        "min_investment": 500,
    },
    ProductCode.ULIP: {
        "name": "ULIP",
        "code": "ulip",
        "default_return": 8.0,
        "risk_level": RiskLevel.MEDIUM,
        "supports_monthly": False,
        "supports_yearly": True,
        "supports_lumpsum": True,
        "tax_type": TaxType.EXEMPT,  # 10(10D) exemption
        "min_investment": 0,
    },
}

# =============================================================================
# GOLD PURITY MAPPING
# =============================================================================

GOLD_PURITY_PERCENTAGE: Dict[str, float] = {
    GoldPurity.K24: 0.999,
    GoldPurity.K22: 0.916,
    GoldPurity.K18: 0.75,
    GoldPurity.K14: 0.583,
    GoldPurity.K13: 0.542,
}

# Default gold price per gram (24K)
DEFAULT_GOLD_PRICE_PER_GRAM: float = 7500.0
DEFAULT_GOLD_INFLATION_RATE: float = 8.0  # Gold price appreciation

# =============================================================================
# WEDDING PRICING TABLE
# =============================================================================

WEDDING_PRICING: Dict[str, Dict[str, float]] = {
    WeddingType.INTIMATE: {
        PackageTier.STANDARD: 500000,
        PackageTier.PREMIUM: 1000000,
        PackageTier.DIAMOND: 2000000,
    },
    WeddingType.SIMPLE: {
        PackageTier.STANDARD: 1000000,
        PackageTier.PREMIUM: 2000000,
        PackageTier.DIAMOND: 4000000,
    },
    WeddingType.TRADITIONAL: {
        PackageTier.STANDARD: 2000000,
        PackageTier.PREMIUM: 4000000,
        PackageTier.DIAMOND: 8000000,
    },
    WeddingType.DESTINATION: {
        PackageTier.STANDARD: 3000000,
        PackageTier.PREMIUM: 6000000,
        PackageTier.DIAMOND: 15000000,
    },
    WeddingType.GRAND: {
        PackageTier.STANDARD: 5000000,
        PackageTier.PREMIUM: 10000000,
        PackageTier.DIAMOND: 25000000,
    },
}

# =============================================================================
# VACATION DESTINATIONS
# =============================================================================

VACATION_DESTINATIONS: Dict[str, Dict[str, Any]] = {
    "dubai": {"name": "Dubai", "base_price": 85000, "type": VacationType.INTERNATIONAL},
    "paris": {"name": "Paris", "base_price": 120000, "type": VacationType.INTERNATIONAL},
    "maldives": {"name": "Maldives", "base_price": 150000, "type": VacationType.INTERNATIONAL},
    "singapore": {"name": "Singapore", "base_price": 90000, "type": VacationType.INTERNATIONAL},
    "thailand": {"name": "Thailand", "base_price": 60000, "type": VacationType.INTERNATIONAL},
    "switzerland": {"name": "Switzerland", "base_price": 200000, "type": VacationType.INTERNATIONAL},
    "bali": {"name": "Bali", "base_price": 80000, "type": VacationType.INTERNATIONAL},
    "europe": {"name": "Europe Tour", "base_price": 250000, "type": VacationType.INTERNATIONAL},
    "goa": {"name": "Goa", "base_price": 25000, "type": VacationType.DOMESTIC},
    "kashmir": {"name": "Kashmir", "base_price": 35000, "type": VacationType.DOMESTIC},
    "kerala": {"name": "Kerala", "base_price": 30000, "type": VacationType.DOMESTIC},
    "rajasthan": {"name": "Rajasthan", "base_price": 28000, "type": VacationType.DOMESTIC},
    "himachal": {"name": "Himachal Pradesh", "base_price": 25000, "type": VacationType.DOMESTIC},
    "andaman": {"name": "Andaman Islands", "base_price": 45000, "type": VacationType.DOMESTIC},
}

VACATION_PACKAGE_MULTIPLIERS: Dict[str, float] = {
    VacationPackageType.STANDARD: 1.0,
    VacationPackageType.PREMIUM: 1.6,
    VacationPackageType.BUSINESS: 2.5,
}

# Price breakdown percentages for vacation
VACATION_PRICE_BREAKDOWN: Dict[str, float] = {
    "flights": 0.35,
    "hotels": 0.30,
    "activities": 0.12,
    "transfers": 0.08,
    "meals": 0.08,
    "visa": 0.04,
    "insurance": 0.03,
}

# =============================================================================
# LOAN DEFAULTS BY TYPE
# =============================================================================

LOAN_DEFAULTS: Dict[str, Dict[str, Any]] = {
    LoanType.HOME: {
        "name": "Home Loan",
        "icon": "🏠",
        "default_rate": 8.5,
        "max_tenure_months": 360,
        "default_tenure_months": 240,
    },
    LoanType.CAR: {
        "name": "Car Loan",
        "icon": "🚗",
        "default_rate": 9.5,
        "max_tenure_months": 84,
        "default_tenure_months": 60,
    },
    LoanType.PERSONAL: {
        "name": "Personal Loan",
        "icon": "💳",
        "default_rate": 12.0,
        "max_tenure_months": 60,
        "default_tenure_months": 36,
    },
    LoanType.EDUCATION: {
        "name": "Education Loan",
        "icon": "🎓",
        "default_rate": 10.0,
        "max_tenure_months": 180,
        "default_tenure_months": 84,
    },
    LoanType.BUSINESS: {
        "name": "Business Loan",
        "icon": "💼",
        "default_rate": 11.0,
        "max_tenure_months": 84,
        "default_tenure_months": 48,
    },
    LoanType.GOLD: {
        "name": "Gold Loan",
        "icon": "🥇",
        "default_rate": 7.5,
        "max_tenure_months": 36,
        "default_tenure_months": 24,
    },
    LoanType.TWO_WHEELER: {
        "name": "Two-Wheeler Loan",
        "icon": "🏍️",
        "default_rate": 10.5,
        "max_tenure_months": 48,
        "default_tenure_months": 36,
    },
    LoanType.OTHER: {
        "name": "Other Loan",
        "icon": "📄",
        "default_rate": 10.0,
        "max_tenure_months": 60,
        "default_tenure_months": 36,
    },
}

# =============================================================================
# INDIAN BANKS LIST
# =============================================================================

INDIAN_BANKS: List[str] = [
    "State Bank of India (SBI)",
    "HDFC Bank",
    "ICICI Bank",
    "Axis Bank",
    "Punjab National Bank (PNB)",
    "Bank of Baroda",
    "Kotak Mahindra Bank",
    "Yes Bank",
    "IndusInd Bank",
    "Union Bank of India",
    "Canara Bank",
    "Bank of India",
    "Indian Bank",
    "Central Bank of India",
    "Indian Overseas Bank",
    "UCO Bank",
    "Federal Bank",
    "IDBI Bank",
    "Karnataka Bank",
    "South Indian Bank",
    "Bandhan Bank",
    "RBL Bank",
    "IDFC First Bank",
    "AU Small Finance Bank",
    "Ujjivan Small Finance Bank",
    "Equitas Small Finance Bank",
    "Other",
]

# =============================================================================
# VEHICLE DATABASE
# =============================================================================

VEHICLE_BRANDS: Dict[str, Dict[str, Any]] = {
    # Cars
    "maruti": {"name": "Maruti Suzuki", "type": VehicleType.CAR, "is_luxury": False},
    "hyundai": {"name": "Hyundai", "type": VehicleType.CAR, "is_luxury": False},
    "tata": {"name": "Tata Motors", "type": VehicleType.CAR, "is_luxury": False},
    "mahindra": {"name": "Mahindra", "type": VehicleType.CAR, "is_luxury": False},
    "honda": {"name": "Honda", "type": VehicleType.CAR, "is_luxury": False},
    "toyota": {"name": "Toyota", "type": VehicleType.CAR, "is_luxury": False},
    "kia": {"name": "Kia", "type": VehicleType.CAR, "is_luxury": False},
    "mercedes": {"name": "Mercedes-Benz", "type": VehicleType.CAR, "is_luxury": True},
    "bmw": {"name": "BMW", "type": VehicleType.CAR, "is_luxury": True},
    "audi": {"name": "Audi", "type": VehicleType.CAR, "is_luxury": True},
    # Bikes
    "hero": {"name": "Hero MotoCorp", "type": VehicleType.BIKE, "is_luxury": False},
    "bajaj": {"name": "Bajaj Auto", "type": VehicleType.BIKE, "is_luxury": False},
    "tvs": {"name": "TVS Motor", "type": VehicleType.BIKE, "is_luxury": False},
    "honda_bike": {"name": "Honda Motorcycle", "type": VehicleType.BIKE, "is_luxury": False},
    "royal_enfield": {"name": "Royal Enfield", "type": VehicleType.BIKE, "is_luxury": False},
    "ktm": {"name": "KTM", "type": VehicleType.BIKE, "is_luxury": True},
    "yamaha": {"name": "Yamaha", "type": VehicleType.BIKE, "is_luxury": False},
    "suzuki_bike": {"name": "Suzuki Motorcycle", "type": VehicleType.BIKE, "is_luxury": False},
}

# =============================================================================
# EDUCATION DEFAULTS
# =============================================================================

EDUCATION_INFLATION_RATE: float = 10.0  # Education inflation

DEFAULT_EDUCATION_GOALS: List[Dict[str, Any]] = [
    {"name": "8th – 10th STD", "goal_age": 13, "current_cost": 300000},
    {"name": "11th – 12th STD", "goal_age": 16, "current_cost": 500000},
    {"name": "Under Graduation", "goal_age": 18, "current_cost": 1600000},
    {"name": "Post Graduation", "goal_age": 22, "current_cost": 2000000},
]

# =============================================================================
# RETIREMENT DEFAULTS
# =============================================================================

DEFAULT_RETIREMENT_ASSUMPTIONS: Dict[str, float] = {
    "pre_retirement_inflation": 6.0,
    "post_retirement_inflation": 6.0,
    "return_on_kitty": 7.0,
    "step_up_amount": 2500,  # Monthly
    "step_up_percent": 10.0,
}

CURRENT_INVESTMENT_PRODUCTS: List[str] = [
    ProductCode.MUTUAL_FUND,
    ProductCode.STOCKS,
    ProductCode.FIXED_DEPOSIT,
    ProductCode.RECURRING_DEPOSIT,
    ProductCode.EPF,
    ProductCode.NPS,
    ProductCode.GOLD,
    ProductCode.SAVINGS,
]

# Step-up yearly discount factors (approximations from Lovable)
STEP_UP_YEARLY_DISCOUNT_RUPEE: float = 0.85
STEP_UP_YEARLY_DISCOUNT_PERCENT: float = 0.80

# =============================================================================
# SWP CONSTANTS
# =============================================================================

SWP_MONTHS_PER_YEAR: int = 12

# =============================================================================
# CASH SURPLUS FIELD CATEGORIES
# =============================================================================

CASH_SURPLUS_INCOME_FIELDS: List[str] = ["salary", "rent_income", "dividend", "interest"]

CASH_SURPLUS_INSURANCE_FIELDS: List[str] = [
    "life_insurance", "health_insurance", "motor_insurance", "other_insurance"
]

CASH_SURPLUS_SAVINGS_FIELDS: List[str] = [
    "mf", "stocks", "rd", "fd", "ncd", "gold", "pf", "ppf", "nps", "savings_ac", "ulip"
]

CASH_SURPLUS_LOAN_TYPES: List[str] = [
    "home_loan", "personal_loan", "vehicle_loan", "education_loan", "consumer_loan"
]

CASH_SURPLUS_EXPENSE_CATEGORIES: Dict[str, List[str]] = {
    "household": ["rent_maintenance", "electricity"],
    "ration": ["ration", "lpg"],
    "medicine": ["medicine"],
    "transport": ["vehicle_maintenance", "petrol"],
    "entertainment": ["shopping", "food", "ott"],
    "other_household": ["househelp", "religious", "club"],
    "miscellaneous": ["vacations", "misc_other"],
    "education": ["school_fees", "tuition", "child_travel", "pocket_money"],
}

# =============================================================================
# CALCULATION PRECISION
# =============================================================================

CALCULATION_PRECISION: int = 2  # Decimal places for monetary values
BINARY_SEARCH_ITERATIONS: int = 100  # For reverse SIP calculations
BINARY_SEARCH_TOLERANCE: float = 1.0  # ₹1 tolerance

# Loan calculation constants
LOAN_BALANCE_PRECISION: float = 0.01  # Loan paid off threshold
AMORTIZATION_MAX_MONTHS: int = 600  # Safety limit (50 years)

# =============================================================================
# DEFAULT VALUES BY CALCULATOR
# =============================================================================

CALCULATOR_DEFAULTS: Dict[str, Dict[str, Any]] = {
    CalculatorType.SIP_LUMPSUM_GOAL: {
        "monthly_sip": 10000,
        "lumpsum_amount": 100000,
        "target_amount": 1000000,
        "tenure_years": 15,
        "expected_return": 12.65,
        "inflation_rate": 6.0,
        "step_up_percent": 10,
        "step_up_amount": 1000,
    },
    CalculatorType.VEHICLE: {
        "vehicle_price": 800000,
        "down_payment_percent": 20,
        "loan_interest_rate": 9.5,
        "loan_tenure_months": 60,
        "expected_return": 12.0,
    },
    CalculatorType.VACATION: {
        "destination": "dubai",
        "travelers": 2,
        "package_type": VacationPackageType.STANDARD,
        "years_to_goal": 2,
        "inflation_rate": 6.0,
    },
    CalculatorType.EDUCATION: {
        "child_current_age": 5,
        "education_inflation": 10.0,
        "expected_return": 12.0,
    },
    CalculatorType.WEDDING: {
        "wedding_type": WeddingType.TRADITIONAL,
        "package_tier": PackageTier.STANDARD,
        "years_to_goal": 5,
        "inflation_rate": 6.0,
    },
    CalculatorType.GOLD: {
        "quantity": 50,
        "unit": GoldUnit.GRAMS,
        "purity": GoldPurity.K22,
        "price_per_gram": 7500,
        "years_to_goal": 4,
        "inflation_rate": 8.0,
    },
    CalculatorType.RETIREMENT: {
        "current_age": 30,
        "retirement_age": 60,
        "life_expectancy": 80,
        "monthly_expense": 50000,
        "pre_retirement_inflation": 6.0,
        "post_retirement_inflation": 6.0,
        "return_on_kitty": 7.0,
    },
    CalculatorType.SWP: {
        "principal": 5000000,
        "monthly_withdrawal": 40000,
        "accumulation_years": 5,
        "withdrawal_years": 10,
        "expected_return": 10.0,
        "fund_type": FundType.EQUITY,
    },
    CalculatorType.PREPAYMENT: {
        "loan_amount": 5000000,
        "interest_rate": 8.5,
        "tenure_months": 120,
        "loan_type": LoanType.HOME,
    },
    CalculatorType.CASH_SURPLUS: {
        # No specific defaults, all fields start at 0
    },
}