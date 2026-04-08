"""
Calculator Models
Pydantic models for all 10 calculators with dual-mode (target_based/investment_based) support.
Aligned with database schema and Lovable frontend specs.
"""

from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator

from app.constants.calculator_constants import (
    CalculatorType,
    CalculationMode,
    InvestmentFrequency,
    ProductCode,
    TaxType,
    RiskLevel,
    VehicleType,
    VehicleCommercialType,
    GoldPurity,
    GoldPurpose,
    GoldUnit,
    WeddingType,
    PackageTier,
    VacationType,
    VacationPackageType,
    FundType,
    LoanType,
    PrepaymentStrategy,
    StepUpType,
    StepUpFrequency,
    SIPMode,
    INVESTMENT_PRODUCTS,
    CALCULATOR_DEFAULTS,
)


# =============================================================================
# SHARED BASE MODELS
# =============================================================================

class ProductSelection(BaseModel):
    """Investment product selection with allocation and return rate"""
    product_code: ProductCode
    allocation: float = Field(ge=0, le=100, description="Allocation percentage (0-100)")
    return_rate: Optional[float] = Field(
        default=None, ge=0, le=50,
        description="Custom return rate. If None, uses product default"
    )
    
    @property
    def effective_return_rate(self) -> float:
        """Get effective return rate (custom or default)"""
        if self.return_rate is not None:
            return self.return_rate
        product = INVESTMENT_PRODUCTS.get(self.product_code)
        return product["default_return"] if product else 12.0


class LoanConfig(BaseModel):
    """Loan configuration for gap financing"""
    enabled: bool = False
    loan_amount: Optional[float] = Field(default=None, ge=0, description="Auto-calculated from gap if not provided")
    interest_rate: float = Field(default=12.0, ge=1, le=30, description="Annual interest rate %")
    tenure_months: int = Field(default=60, ge=6, le=360, description="Loan tenure in months")
    loan_type: LoanType = LoanType.PERSONAL


class LoanOutput(BaseModel):
    """Loan calculation output"""
    loan_amount: float
    interest_rate: float
    tenure_months: int
    emi: float
    total_interest: float
    total_payment: float
    loan_type: LoanType


class EMIScheduleItem(BaseModel):
    """Single row of EMI amortization schedule"""
    month: int
    emi: float
    principal: float
    interest: float
    balance: float
    prepayment: float = 0
    date: Optional[date] = None


class TaxBreakdown(BaseModel):
    """Tax calculation breakdown"""
    total_gains: float = 0
    short_term_gains: float = 0
    long_term_gains: float = 0
    stcg_tax: float = 0
    ltcg_tax: float = 0
    ltcg_exemption: float = 0
    total_tax: float = 0
    effective_tax_rate: float = 0
    post_tax_value: float = 0


class InvestmentOption(BaseModel):
    """Investment option output (monthly/yearly/lumpsum)"""
    monthly: Optional[float] = None
    yearly: Optional[float] = None
    one_time: Optional[float] = None


# =============================================================================
# BASE CALCULATOR REQUEST/RESPONSE
# =============================================================================

class BaseCalculatorRequest(BaseModel):
    """Base request model with common fields"""
    calculation_mode: CalculationMode = CalculationMode.TARGET_BASED
    
    # Investment-based mode fields (when user says "I can invest X")
    investment_amount: Optional[float] = Field(
        default=None, ge=0,
        description="Amount user can invest (for investment_based mode)"
    )
    investment_frequency: InvestmentFrequency = InvestmentFrequency.MONTHLY
    
    # Loan for gap (applies to investment_based mode)
    loan_config: Optional[LoanConfig] = None
    
    # Product selection
    products: List[ProductSelection] = Field(
        default_factory=lambda: [ProductSelection(product_code=ProductCode.MUTUAL_FUND, allocation=100)]
    )
    
    @model_validator(mode="after")
    def validate_investment_mode(self):
        if self.calculation_mode == CalculationMode.INVESTMENT_BASED:
            if self.investment_amount is None or self.investment_amount <= 0:
                raise ValueError("investment_amount is required for investment_based mode")
        return self


class BaseCalculatorResponse(BaseModel):
    """Base response model with common fields"""
    calculator_type: CalculatorType
    calculation_mode: CalculationMode
    
    # Weighted return from product selection
    weighted_return: float
    supports_monthly: bool
    
    # Target-based outputs
    target_amount: Optional[float] = None
    required_monthly: Optional[float] = None
    required_yearly: Optional[float] = None
    required_lumpsum: Optional[float] = None
    
    # Investment-based outputs
    investment_amount: Optional[float] = None
    investment_frequency: Optional[InvestmentFrequency] = None
    projected_corpus: Optional[float] = None
    corpus_covers_percent: Optional[float] = None
    gap_amount: Optional[float] = None
    
    # Loan output (if gap exists and loan enabled)
    loan_details: Optional[LoanOutput] = None
    total_monthly_outflow: Optional[float] = None  # SIP + EMI
    
    # Tax breakdown
    tax_breakdown: Optional[TaxBreakdown] = None


# =============================================================================
# 1. SIP / LUMPSUM / GOAL UNIFIED CALCULATOR
# =============================================================================

class SIPLumpsumGoalRequest(BaseCalculatorRequest):
    """
    Unified SIP/Lumpsum/Goal Calculator Input.
    
    Modes:
    - sip: Calculate corpus from monthly SIP
    - lumpsum: Calculate corpus from one-time investment
    - goal_sip: Calculate required SIP for target
    - goal_lumpsum: Calculate required lumpsum for target
    - goal_both: Show both SIP and lumpsum options for target
    """
    calculator_type: CalculatorType = CalculatorType.SIP_LUMPSUM_GOAL
    
    # Mode selection
    mode: SIPMode = Field(default=SIPMode.SIP, description="Calculator mode")
    
    # Common inputs
    tenure_years: int = Field(default=15, ge=1, le=50, description="Investment tenure in years")
    expected_return: float = Field(default=12.0, ge=1, le=30, description="Expected annual return %")
    
    # SIP mode inputs
    monthly_sip: Optional[float] = Field(default=None, ge=100, description="Monthly SIP amount (for sip mode)")
    
    # Lumpsum mode inputs
    lumpsum_amount: Optional[float] = Field(default=None, ge=1000, description="One-time investment (for lumpsum mode)")
    
    # Goal mode inputs
    target_amount: Optional[float] = Field(default=None, ge=1000, description="Target corpus (for goal modes)")
    inflation_rate: float = Field(default=6.0, ge=0, le=20, description="Inflation rate for goal")
    current_savings: float = Field(default=0, ge=0, description="Existing savings")
    
    # Step-up options (for SIP modes)
    step_up_type: StepUpType = StepUpType.NONE
    step_up_amount: Optional[float] = Field(default=None, ge=0, description="Annual step-up in ₹")
    step_up_percentage: Optional[float] = Field(default=None, ge=0, le=100, description="Annual step-up %")
    
    @model_validator(mode="after")
    def validate_mode_inputs(self):
        if self.mode == SIPMode.SIP:
            if self.monthly_sip is None:
                self.monthly_sip = 10000  # Default
        elif self.mode == SIPMode.LUMPSUM:
            if self.lumpsum_amount is None:
                self.lumpsum_amount = 100000  # Default
        elif self.mode in [SIPMode.GOAL_SIP, SIPMode.GOAL_LUMPSUM, SIPMode.GOAL_BOTH]:
            if self.target_amount is None:
                raise ValueError("target_amount is required for goal modes")
        return self


class SIPLumpsumGoalResponse(BaseCalculatorResponse):
    """Unified SIP/Lumpsum/Goal Calculator Output"""
    calculator_type: CalculatorType = CalculatorType.SIP_LUMPSUM_GOAL
    
    # Mode used
    mode: SIPMode
    
    # Common outputs
    tenure_years: int
    expected_return: float
    
    # SIP mode outputs
    monthly_sip: Optional[float] = None
    total_sip_investment: Optional[float] = None
    sip_corpus: Optional[float] = None
    sip_returns: Optional[float] = None
    sip_returns_percentage: Optional[float] = None
    
    # Lumpsum mode outputs
    lumpsum_amount: Optional[float] = None
    lumpsum_corpus: Optional[float] = None
    lumpsum_returns: Optional[float] = None
    lumpsum_returns_percentage: Optional[float] = None
    growth_multiplier: Optional[float] = None
    
    # Goal mode outputs
    target_amount: Optional[float] = None
    future_value: Optional[float] = None  # Inflation-adjusted target
    current_savings_fv: Optional[float] = None
    amount_to_accumulate: Optional[float] = None
    
    # Required investments (for goal modes)
    required_monthly_sip: Optional[float] = None
    required_lumpsum: Optional[float] = None
    required_yearly: Optional[float] = None
    
    # Step-up options
    step_up_type: Optional[StepUpType] = None
    step_up_sip_corpus: Optional[float] = None
    step_up_total_investment: Optional[float] = None
    required_step_up_sip: Optional[float] = None  # Starting SIP for step-up mode
    
    # Investment options (for goal modes)
    normal: Optional[InvestmentOption] = None
    step_up_amount_option: Optional[InvestmentOption] = None
    step_up_percent_option: Optional[InvestmentOption] = None
    
    # Year-wise breakdown
    year_wise_breakdown: Optional[List[Dict[str, Any]]] = None


# =============================================================================
# 2. VEHICLE CALCULATOR
# =============================================================================

class VehicleInput(BaseModel):
    """Single vehicle configuration"""
    vehicle_type: VehicleType
    brand: Optional[str] = None
    model: Optional[str] = None
    price: float = Field(ge=10000)
    commercial_type: Optional[VehicleCommercialType] = None


class VehicleCalculatorRequest(BaseCalculatorRequest):
    """Vehicle Calculator Input"""
    calculator_type: CalculatorType = CalculatorType.VEHICLE
    
    # Vehicle details
    vehicle: VehicleInput
    comparison_vehicle: Optional[VehicleInput] = None  # For comparison mode
    
    # Timeline
    years_to_purchase: int = Field(default=3, ge=1, le=15)
    inflation_rate: float = Field(default=5.0, ge=0, le=20)
    
    # Down payment & loan
    down_payment_percent: float = Field(default=20, ge=0, le=100)
    loan_interest_rate: float = Field(default=9.5, ge=1, le=25)
    loan_tenure_months: int = Field(default=60, ge=12, le=84)


class VehicleCalculatorResponse(BaseCalculatorResponse):
    """Vehicle Calculator Output"""
    calculator_type: CalculatorType = CalculatorType.VEHICLE
    
    # Vehicle details
    vehicle_type: VehicleType
    current_price: float
    future_price: float  # Inflated
    
    # Down payment
    down_payment_amount: float
    down_payment_required: InvestmentOption
    
    # Loan details
    loan_amount: float
    loan_emi: float
    total_loan_interest: float
    total_loan_payment: float
    
    # Total cost of ownership
    total_cost: float
    
    # Comparison (if applicable)
    comparison: Optional[Dict[str, Any]] = None
    
    # Amortization schedule
    emi_schedule: Optional[List[EMIScheduleItem]] = None


# =============================================================================
# 5. VACATION CALCULATOR
# =============================================================================

class VacationCalculatorRequest(BaseCalculatorRequest):
    """Vacation Calculator Input"""
    calculator_type: CalculatorType = CalculatorType.VACATION
    
    # Destination & package
    destination_id: str = Field(description="Destination key from VACATION_DESTINATIONS")
    package_type: VacationPackageType = VacationPackageType.STANDARD
    travelers: int = Field(default=2, ge=1, le=20)
    
    # Custom pricing (overrides destination base price)
    custom_budget: Optional[float] = Field(default=None, ge=0)
    
    # Timeline
    years_to_goal: int = Field(default=2, ge=1, le=15)
    inflation_rate: float = Field(default=6.0, ge=0, le=20)
    
    # Current savings
    current_savings: float = Field(default=0, ge=0)


class VacationCalculatorResponse(BaseCalculatorResponse):
    """Vacation Calculator Output"""
    calculator_type: CalculatorType = CalculatorType.VACATION
    
    destination: str
    destination_name: str
    package_type: VacationPackageType
    travelers: int
    
    # Pricing
    base_price_per_person: float
    total_current_cost: float
    total_future_cost: float  # Inflated
    
    # Price breakdown
    price_breakdown: Dict[str, float]
    
    # Savings impact
    current_savings_fv: float
    amount_to_accumulate: float
    
    # Investment options
    investment_options: InvestmentOption
    
    # Affordability
    can_afford: bool
    shortfall: Optional[float] = None


# =============================================================================
# 6. EDUCATION CALCULATOR
# =============================================================================

class EducationGoalInput(BaseModel):
    """Single education goal"""
    name: str
    goal_age: int = Field(ge=1, le=35)
    current_cost: float = Field(ge=0)
    accumulated_amount: float = Field(default=0, ge=0)
    accumulated_receive_immediately: bool = True
    accumulated_receive_at_age: Optional[int] = None


class ChildInput(BaseModel):
    """Child configuration for education planning"""
    name: str = "Child 1"
    current_age: int = Field(ge=0, le=25)
    goals: List[EducationGoalInput] = Field(default_factory=list)
    products: List[ProductSelection] = Field(
        default_factory=lambda: [ProductSelection(product_code=ProductCode.MUTUAL_FUND, allocation=100)]
    )
    custom_return_rate: Optional[float] = Field(default=None, ge=0, le=30)


class EducationCalculatorRequest(BaseCalculatorRequest):
    """Education Calculator Input"""
    calculator_type: CalculatorType = CalculatorType.EDUCATION
    
    children: List[ChildInput] = Field(min_length=1)
    education_inflation: float = Field(default=10.0, ge=0, le=20)


class EducationGoalOutput(BaseModel):
    """Output for single education goal"""
    name: str
    goal_age: int
    years_to_goal: int
    current_cost: float
    future_value: float
    adjusted_future_value: float  # After accumulated amount
    monthly_investment: Optional[float]
    yearly_investment: float
    one_time_investment: float


class ChildSummary(BaseModel):
    """Per-child summary"""
    child_name: str
    return_rate: float
    show_monthly: bool
    goals: List[EducationGoalOutput]
    total_monthly: float
    total_yearly: float
    total_one_time: float
    total_future_corpus: float


class EducationCalculatorResponse(BaseCalculatorResponse):
    """Education Calculator Output"""
    calculator_type: CalculatorType = CalculatorType.EDUCATION
    
    children: List[ChildSummary]
    
    # Global summary
    total_children: int
    total_goals: int
    grand_total_monthly: float
    grand_total_yearly: float
    grand_total_one_time: float
    grand_total_corpus: float


# =============================================================================
# 7. WEDDING CALCULATOR
# =============================================================================

class WeddingCalculatorRequest(BaseCalculatorRequest):
    """Wedding Calculator Input"""
    calculator_type: CalculatorType = CalculatorType.WEDDING
    
    # Wedding type & package
    wedding_type: WeddingType
    package_tier: PackageTier
    
    # Or custom cost
    custom_cost: Optional[float] = Field(default=None, ge=0)
    
    # Timeline
    years_to_goal: int = Field(default=5, ge=1, le=15)
    inflation_rate: float = Field(default=6.0, ge=0, le=20)
    
    # Accumulated savings
    accumulated_amount: float = Field(default=0, ge=0)
    accumulated_receive_immediately: bool = True
    accumulated_receive_at_age: Optional[int] = None


class WeddingCalculatorResponse(BaseCalculatorResponse):
    """Wedding Calculator Output"""
    calculator_type: CalculatorType = CalculatorType.WEDDING
    
    wedding_type: WeddingType
    package_tier: PackageTier
    
    # Costs
    current_cost: float
    future_cost: float
    accumulated_fv: float
    amount_needed: float
    
    # Investment options
    investment_options: InvestmentOption
    
    # Product breakdown
    product_breakdown: Optional[List[Dict[str, Any]]] = None


# =============================================================================
# 8. GOLD CALCULATOR
# =============================================================================

class GoldCalculatorRequest(BaseCalculatorRequest):
    """Gold Calculator Input"""
    calculator_type: CalculatorType = CalculatorType.GOLD
    
    # Gold details
    purpose: GoldPurpose = GoldPurpose.JEWELLERY
    purity: GoldPurity = GoldPurity.K22
    quantity: float = Field(ge=0.1, description="Quantity in grams or kg")
    unit: GoldUnit = GoldUnit.GRAMS
    price_per_gram: float = Field(default=7500, ge=1000, description="Current 24K price per gram")
    
    # Timeline
    years_to_goal: int = Field(default=4, ge=1, le=30)
    inflation_rate: float = Field(default=8.0, ge=0, le=20, description="Gold price appreciation")


class GoldCalculatorResponse(BaseCalculatorResponse):
    """Gold Calculator Output"""
    calculator_type: CalculatorType = CalculatorType.GOLD
    
    purpose: GoldPurpose
    purity: GoldPurity
    quantity_grams: float
    purity_percentage: float
    
    # Pricing
    current_price_per_gram: float  # Adjusted for purity
    current_target_value: float
    future_target_value: float  # Inflated (YOUR CHANGE #1)
    
    # Investment options
    investment_options: InvestmentOption
    
    # Projected corpus (YOUR CHANGE #2)
    projected_corpus: float  # What investment will grow to
    
    # Product breakdown with tax
    product_breakdown: Optional[List[Dict[str, Any]]] = None


# =============================================================================
# 9. RETIREMENT CALCULATOR
# =============================================================================

class IrregularCashFlow(BaseModel):
    """Irregular cash flow entry (bonus, rental income, etc.)"""
    amount: float = Field(ge=0)
    times_per_year: int = Field(ge=1, le=12)
    product_code: ProductCode = ProductCode.MUTUAL_FUND


class ExpectedLumpsum(BaseModel):
    """Expected lumpsum entry (inheritance, property sale, etc.)"""
    amount: float = Field(ge=0)
    at_age: int = Field(ge=0)
    product_code: ProductCode = ProductCode.MUTUAL_FUND


class CurrentInvestment(BaseModel):
    """Current investment holding"""
    product_code: ProductCode
    amount: float = Field(default=0, ge=0)
    return_rate: Optional[float] = Field(default=None, ge=0, le=50)


class RetirementAssumptions(BaseModel):
    """Retirement calculation assumptions"""
    pre_retirement_inflation: float = Field(default=6.0, ge=0, le=20)
    post_retirement_inflation: float = Field(default=6.0, ge=0, le=20)
    return_on_kitty: float = Field(default=7.0, ge=0, le=20)
    step_up_amount: float = Field(default=2500, ge=0, description="Monthly step-up amount")
    step_up_percent: float = Field(default=10.0, ge=0, le=100)


class RetirementCalculatorRequest(BaseCalculatorRequest):
    """Retirement Calculator Input"""
    calculator_type: CalculatorType = CalculatorType.RETIREMENT
    
    # Age details
    current_age: int = Field(ge=18, le=100)
    retirement_age: int = Field(ge=30, le=100)
    life_expectancy: int = Field(ge=50, le=120)
    
    # Expense
    current_monthly_expense: float = Field(ge=0)
    
    # Current investments
    current_investments: List[CurrentInvestment] = Field(default_factory=list)
    
    # Additional cash flows
    irregular_cash_flows: List[IrregularCashFlow] = Field(default_factory=list)
    expected_lumpsums: List[ExpectedLumpsum] = Field(default_factory=list)
    
    # Assumptions
    assumptions: RetirementAssumptions = Field(default_factory=RetirementAssumptions)
    
    @model_validator(mode="after")
    def validate_ages(self):
        if self.retirement_age <= self.current_age:
            raise ValueError("retirement_age must be greater than current_age")
        if self.life_expectancy <= self.retirement_age:
            raise ValueError("life_expectancy must be greater than retirement_age")
        return self


class RetirementCalculatorResponse(BaseCalculatorResponse):
    """Retirement Calculator Output"""
    calculator_type: CalculatorType = CalculatorType.RETIREMENT
    
    # Timeline
    years_to_retirement: int
    retirement_years: int
    
    # Expense projection
    expense_at_retirement: float  # Monthly
    
    # Corpus
    corpus_needed: float
    future_value_of_savings: float
    shortfall: float  # Can be negative (surplus)
    is_surplus: bool
    
    # Investment options (if shortfall)
    normal: Optional[InvestmentOption] = None
    step_up_amount: Optional[InvestmentOption] = None
    step_up_percent: Optional[InvestmentOption] = None


# =============================================================================
# 10. SWP CALCULATOR
# =============================================================================

class SWPCalculatorRequest(BaseCalculatorRequest):
    """SWP (Systematic Withdrawal Plan) Calculator Input"""
    calculator_type: CalculatorType = CalculatorType.SWP
    
    # Investment details
    principal: float = Field(default=5000000, ge=100000, le=500000000)
    monthly_withdrawal: float = Field(default=40000, ge=0)
    
    # Timeline
    accumulation_years: int = Field(default=5, ge=0, le=30, description="Years before SWP starts")
    withdrawal_years: int = Field(default=10, ge=1, le=30)
    
    # Returns
    expected_return: float = Field(default=10.0, ge=1, le=20)
    
    # Fund type (for tax calculation)
    fund_type: FundType = FundType.EQUITY
    
    # Step-up withdrawal
    annual_withdrawal_increase: float = Field(default=0, ge=0, le=20, description="Annual increase in withdrawal %")


class WithdrawalBreakdown(BaseModel):
    """Monthly withdrawal breakdown"""
    month: int
    year: int
    opening_balance: float
    withdrawal: float
    capital_gain_in_withdrawal: float
    principal_in_withdrawal: float
    closing_balance: float
    is_short_term: bool


class YearlySummary(BaseModel):
    """Yearly withdrawal summary"""
    year: int
    month_range: str
    opening_balance: float
    total_withdrawal: float
    closing_balance: float
    stcg_amount: float
    ltcg_amount: float
    stcg_tax: float
    ltcg_tax: float
    net_amount: float


class SWPCalculatorResponse(BaseCalculatorResponse):
    """SWP Calculator Output"""
    calculator_type: CalculatorType = CalculatorType.SWP
    
    # Accumulation phase
    value_at_swp_start: float
    total_growth_during_accumulation: float
    
    # Withdrawal phase
    total_withdrawals: float
    number_of_withdrawals: int
    final_balance: float
    total_gain: float
    
    # Net after tax
    net_amount_after_tax: float
    
    # Tax breakdown
    tax_breakdown: TaxBreakdown
    
    # Schedules
    yearly_summary: List[YearlySummary]
    withdrawal_breakdown: Optional[List[WithdrawalBreakdown]] = None


# =============================================================================
# 11. PREPAYMENT CALCULATOR
# =============================================================================

class PrepaymentEntry(BaseModel):
    """Single prepayment entry"""
    amount: float = Field(ge=0)
    date: date
    
    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        if v < date.today():
            pass  # Allow past dates for existing prepayments
        return v


class PrepaymentCalculatorRequest(BaseCalculatorRequest):
    """Loan Prepayment Calculator Input"""
    calculator_type: CalculatorType = CalculatorType.PREPAYMENT
    
    # Loan details
    loan_amount: float = Field(ge=10000)
    interest_rate: float = Field(ge=1, le=30)
    tenure_months: int = Field(ge=12, le=360)
    start_date: date = Field(default_factory=date.today)
    
    # Loan metadata
    loan_type: LoanType = LoanType.HOME
    bank_name: Optional[str] = None
    
    # Prepayments
    prepayments: List[PrepaymentEntry] = Field(default_factory=list)
    
    # Accelerated EMI
    extra_emis_per_year: int = Field(default=0, ge=0, le=4)


class PrepaymentScenario(BaseModel):
    """Single prepayment scenario output"""
    emi: float
    total_months: int
    total_interest: float
    total_payment: float
    interest_saved: float
    months_saved: int
    schedule: Optional[List[EMIScheduleItem]] = None


class PrepaymentCalculatorResponse(BaseCalculatorResponse):
    """Prepayment Calculator Output"""
    calculator_type: CalculatorType = CalculatorType.PREPAYMENT
    
    # Original loan
    loan_amount: float
    interest_rate: float
    tenure_months: int
    
    # Scenarios
    original: PrepaymentScenario
    reduced_tenure: PrepaymentScenario
    reduced_emi: PrepaymentScenario
    accelerated: Optional[PrepaymentScenario] = None
    
    # Recommendation
    recommendation: PrepaymentStrategy
    max_interest_saved: float


# =============================================================================
# 12. CASH SURPLUS CALCULATOR
# =============================================================================

class CashFlowItem(BaseModel):
    """Single cash flow item with amount and frequency"""
    amount: float = Field(default=0, ge=0)
    frequency: InvestmentFrequency = InvestmentFrequency.MONTHLY


class LoanItem(BaseModel):
    """Loan item with EMI and pending amount"""
    emi: float = Field(default=0, ge=0)
    pending: float = Field(default=0, ge=0)
    frequency: InvestmentFrequency = InvestmentFrequency.MONTHLY


class CashSurplusCalculatorRequest(BaseCalculatorRequest):
    """Cash Surplus Calculator Input"""
    calculator_type: CalculatorType = CalculatorType.CASH_SURPLUS
    
    # Income
    income: Dict[str, CashFlowItem] = Field(default_factory=dict)
    
    # Insurance premiums
    insurance: Dict[str, CashFlowItem] = Field(default_factory=dict)
    
    # Savings/investments
    savings: Dict[str, CashFlowItem] = Field(default_factory=dict)
    
    # Loans
    loans: Dict[str, LoanItem] = Field(default_factory=dict)
    
    # Expenses by category
    expenses: Dict[str, CashFlowItem] = Field(default_factory=dict)
    
    # Current investment values (portfolio)
    current_investments: Dict[str, float] = Field(default_factory=dict)


class ExpenseBreakdown(BaseModel):
    """Expense breakdown by category"""
    insurance: float
    savings: float
    loans: float
    education: float
    lifestyle: float
    total: float


class CashSurplusCalculatorResponse(BaseCalculatorResponse):
    """Cash Surplus Calculator Output"""
    calculator_type: CalculatorType = CalculatorType.CASH_SURPLUS
    
    # Income
    total_income_yearly: float
    total_income_monthly: float
    
    # Expenses
    total_expenses_yearly: float
    total_expenses_monthly: float
    expense_breakdown: ExpenseBreakdown
    
    # Loans
    total_emi_yearly: float
    total_emi_monthly: float
    total_pending_loans: float
    
    # Surplus/Shortfall
    cash_surplus_yearly: float
    cash_surplus_monthly: float
    is_surplus: bool
    
    # Portfolio value
    total_portfolio: float


# =============================================================================
# DATABASE SAVE MODEL
# =============================================================================

class CalculatorResultSave(BaseModel):
    """Model for saving calculator result to database"""
    user_id: UUID
    client_id: Optional[UUID] = None
    goal_id: Optional[UUID] = None
    calculator_type: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    pdf_url: Optional[str] = None


# =============================================================================
# API RESPONSE WRAPPERS
# =============================================================================

class CalculatorAPIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = True
    message: str = "Calculation completed successfully"
    data: Union[
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
    ]
    saved_id: Optional[UUID] = None