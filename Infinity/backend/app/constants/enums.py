"""
Enums matching Supabase PostgreSQL enum types exactly.

RULES:
- Python name: prefixed with 'v_' if starts with digit (Python syntax requirement)
- .value: MUST match DB enum value exactly (this is what gets sent to Supabase)
- Always use enum.value or model_dump(mode="json") when inserting to DB

Auto-generated from Supabase enum definitions.
"""

from enum import Enum


# ──────────────────────────────────────────────
# Common / Shared
# ──────────────────────────────────────────────

class GenderType(str, Enum):
    male = "male"
    female = "female"
    other = "other"


class MaritalStatusType(str, Enum):
    single = "single"
    married = "married"
    divorced = "divorced"
    widower = "widower"
    separated = "separated"
    dont_know = "dont_know"


class OccupationType(str, Enum):
    service = "service"
    business = "business"
    retired = "retired"
    professional = "professional"
    student = "student"
    self_employed = "self_employed"
    housemaker = "housemaker"
    dont_know = "dont_know"


class IncomeGroupType(str, Enum):
    zero = "zero"
    v1_to_2_5 = "1_to_2_5"
    v2_6_to_8_8 = "2_6_to_8_8"
    v8_9_to_12 = "8_9_to_12"
    v12_1_to_24 = "12_1_to_24"
    v24_1_to_48 = "24_1_to_48"
    v48_1_plus = "48_1_plus"
    dont_know = "dont_know"


class AgeGroupType(str, Enum):
    below_18 = "below_18"
    v18_to_24 = "18_to_24"
    v25_to_35 = "25_to_35"
    v36_to_45 = "36_to_45"
    v46_to_55 = "46_to_55"
    v56_plus = "56_plus"
    dont_know = "dont_know"


class SourceType(str, Enum):
    natural_market = "natural_market"
    referral = "referral"
    social_networking = "social_networking"
    business_group = "business_group"
    marketing_activity = "marketing_activity"
    iap = "iap"
    cold_call = "cold_call"
    social_media = "social_media"


# ──────────────────────────────────────────────
# Leads
# ──────────────────────────────────────────────

class LeadStatusType(str, Enum):
    follow_up = "follow_up"
    meeting_scheduled = "meeting_scheduled"
    cancelled = "cancelled"
    converted = "converted"


# ──────────────────────────────────────────────
# Clients
# ──────────────────────────────────────────────

class RiskProfileType(str, Enum):
    conservative = "conservative"
    moderately_conservative = "moderately_conservative"
    moderate = "moderate"
    moderately_aggressive = "moderately_aggressive"
    aggressive = "aggressive"


class AumBracketType(str, Enum):
    less_than_10_lakhs = "less_than_10_lakhs"
    v10_to_25_lakhs = "10_to_25_lakhs"
    v25_to_50_lakhs = "25_to_50_lakhs"
    v50_lakhs_to_1_cr = "50_lakhs_to_1_cr"
    v1_cr_plus = "1_cr_plus"


class SipBracketType(str, Enum):
    zero = "zero"
    upto_5k = "upto_5k"
    v5_1k_to_10k = "5_1k_to_10k"
    v10_1k_to_25k = "10_1k_to_25k"
    v25_1k_to_50k = "25_1k_to_50k"
    v50_1k_to_1_lakh = "50_1k_to_1_lakh"
    v1_lakh_plus = "1_lakh_plus"


class ClientTenureType(str, Enum):
    upto_1_year = "upto_1_year"
    v1_to_3_years = "1_to_3_years"
    v3_to_8_years = "3_to_8_years"
    v8_to_12_years = "8_to_12_years"
    v12_plus_years = "12_plus_years"


# ──────────────────────────────────────────────
# Tasks
# ──────────────────────────────────────────────

class TaskStatusType(str, Enum):
    pending = "pending"
    completed = "completed"
    cancelled = "cancelled"
    carried_forward = "carried_forward"


class TaskPriorityType(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class TaskMediumType(str, Enum):
    call = "call"
    whatsapp = "whatsapp"
    email = "email"
    in_person = "in_person"
    video_call = "video_call"


# ──────────────────────────────────────────────
# Touchpoints
# ──────────────────────────────────────────────

class TouchpointStatusType(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    rescheduled = "rescheduled"


class InteractionType(str, Enum):
    meeting_office = "meeting_office"
    meeting_home = "meeting_home"
    cafe = "cafe"
    restaurant = "restaurant"
    call = "call"
    video_call = "video_call"


# ──────────────────────────────────────────────
# Business Opportunities
# ──────────────────────────────────────────────

class OpportunityStageType(str, Enum):
    identified = "identified"
    inbound = "inbound"
    proposed = "proposed"


class OpportunityTypeEnum(str, Enum):
    sip = "sip"
    lumpsum = "lumpsum"
    swp = "swp"
    ncd = "ncd"
    fd = "fd"
    life_insurance = "life_insurance"
    health_insurance = "health_insurance"
    las = "las"


# Backward-compat alias — old code imports OpportunityType
OpportunityType = OpportunityTypeEnum


class OpportunitySourceType(str, Enum):
    goal_planning = "goal_planning"
    portfolio_rebalancing = "portfolio_rebalancing"
    client_servicing = "client_servicing"
    financial_activities = "financial_activities"


class BOOutcomeType(str, Enum):
    open = "open"
    won = "won"
    lost = "lost"


# ──────────────────────────────────────────────
# Products
# ──────────────────────────────────────────────

class ProductCategoryType(str, Enum):
    mutual_fund = "mutual_fund"
    stocks = "stocks"
    fixed_deposit = "fixed_deposit"
    recurring_deposit = "recurring_deposit"
    ppf = "ppf"
    epf = "epf"
    nps = "nps"
    bonds = "bonds"
    ncd = "ncd"
    gold = "gold"
    real_estate = "real_estate"
    term_insurance = "term_insurance"
    health_insurance = "health_insurance"
    pa_insurance = "pa_insurance"
    life_insurance = "life_insurance"
    motor_insurance = "motor_insurance"
    ulip = "ulip"
    pms = "pms"
    aif = "aif"
    las = "las"
    swp = "swp"
    other = "other"


class ProductStatusType(str, Enum):
    active = "active"
    paused = "paused"
    stopped = "stopped"
    redeemed = "redeemed"
    matured = "matured"
    lapsed = "lapsed"
    surrendered = "surrendered"


class InvestmentType(str, Enum):
    sip = "sip"
    lumpsum = "lumpsum"
    both = "both"


# Backward-compat alias — old code imports InvestmentTypeEnum
InvestmentTypeEnum = InvestmentType


class PremiumFrequencyType(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    half_yearly = "half_yearly"
    yearly = "yearly"
    one_time = "one_time"


class FundType(str, Enum):
    equity = "equity"
    debt = "debt"


# ──────────────────────────────────────────────
# Transactions
# ──────────────────────────────────────────────

class TransactionType(str, Enum):
    sip_installment = "sip_installment"
    additional_purchase = "additional_purchase"
    lumpsum = "lumpsum"
    redemption = "redemption"
    partial_redemption = "partial_redemption"
    switch_in = "switch_in"
    switch_out = "switch_out"
    dividend = "dividend"
    premium_paid = "premium_paid"


# Backward-compat alias — old code imports TransactionTypeEnum
TransactionTypeEnum = TransactionType


# ──────────────────────────────────────────────
# Goals
# ──────────────────────────────────────────────

class GoalType(str, Enum):
    retirement = "retirement"
    child_education = "child_education"
    cash_surplus = "cash_surplus"
    lifestyle = "lifestyle"
    other = "other"
    car_purchase = "car_purchase"
    bike_purchase = "bike_purchase"
    vacation = "vacation"
    wedding = "wedding"
    home_renovation = "home_renovation"
    emergency_fund = "emergency_fund"
    wealth_creation = "wealth_creation"
    gold_purchase = "gold_purchase"


class GoalStatusType(str, Enum):
    active = "active"
    on_track = "on_track"
    behind = "behind"
    achieved = "achieved"
    paused = "paused"


class LifestyleSubtype(str, Enum):
    vacation_domestic = "vacation_domestic"
    vacation_international = "vacation_international"
    wedding = "wedding"
    home_renovation = "home_renovation"
    jewellery = "jewellery"
    gadgets = "gadgets"
    emergency_fund = "emergency_fund"
    car = "car"
    bike = "bike"
    other = "other"


class VehicleType(str, Enum):
    car = "car"
    bike = "bike"


# ──────────────────────────────────────────────
# Calculators
# ──────────────────────────────────────────────

class CalculatorType(str, Enum):
    sip_lumpsum_goal = "sip_lumpsum_goal"
    vehicle = "vehicle"
    vacation = "vacation"
    education = "education"
    wedding = "wedding"
    gold = "gold"
    retirement = "retirement"
    swp = "swp"
    prepayment = "prepayment"
    cash_surplus = "cash_surplus"


class CalculationModeType(str, Enum):
    target_based = "target_based"
    investment_based = "investment_based"


class SipModeType(str, Enum):
    sip = "sip"
    lumpsum = "lumpsum"
    goal_sip = "goal_sip"
    goal_lumpsum = "goal_lumpsum"
    goal_both = "goal_both"


class StepUpType(str, Enum):
    none = "none"
    amount = "amount"
    percentage = "percentage"


class PrepaymentStrategyType(str, Enum):
    reduce_tenure = "reduce_tenure"
    reduce_emi = "reduce_emi"


# ──────────────────────────────────────────────
# Gold Calculator
# ──────────────────────────────────────────────

class GoldPurityType(str, Enum):
    v24 = "24"
    v22 = "22"
    v18 = "18"
    v14 = "14"
    v13 = "13"


class GoldPurposeType(str, Enum):
    jewellery = "jewellery"
    coins = "coins"
    bars = "bars"
    investment = "investment"


class GoldUnitType(str, Enum):
    grams = "grams"
    kg = "kg"


# ──────────────────────────────────────────────
# Vacation / Wedding
# ──────────────────────────────────────────────

class VacationPackageType(str, Enum):
    standard = "standard"
    premium = "premium"
    business = "business"


class WeddingType(str, Enum):
    intimate = "intimate"
    simple = "simple"
    traditional = "traditional"
    destination = "destination"
    grand = "grand"


# ──────────────────────────────────────────────
# Loans
# ──────────────────────────────────────────────

class LoanType(str, Enum):
    home = "home"
    car = "car"
    personal = "personal"
    education = "education"
    business = "business"
    gold = "gold"
    two_wheeler = "two_wheeler"
    other = "other"


# ──────────────────────────────────────────────
# Notifications / Communication
# ──────────────────────────────────────────────

class NotificationType(str, Enum):
    morning_schedule = "morning_schedule"
    afternoon_progress = "afternoon_progress"
    eod_summary = "eod_summary"
    greeting_gm = "greeting_gm"
    greeting_ge = "greeting_ge"
    greeting_gn = "greeting_gn"
    task_reminder = "task_reminder"
    meeting_reminder = "meeting_reminder"
    birthday_reminder = "birthday_reminder"


# Backward-compat alias
NotificationTypeEnum = NotificationType


class ChannelType(str, Enum):
    email = "email"
    whatsapp = "whatsapp"


class MessageStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    delivered = "delivered"
    read = "read"
    failed = "failed"


# Backward-compat alias
MessageStatusType = MessageStatus


# ──────────────────────────────────────────────
# Devices
# ──────────────────────────────────────────────

class DeviceType(str, Enum):
    android = "android"
    ios = "ios"
    web = "web"


# ──────────────────────────────────────────────
# Packages
# ──────────────────────────────────────────────

class PackageTierType(str, Enum):
    standard = "standard"
    premium = "premium"
    diamond = "diamond"


# ──────────────────────────────────────────────
# Voice / OCR (not DB enums — used only in app logic)
# ──────────────────────────────────────────────

class VoiceInputStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    NEEDS_CONFIRMATION = "needs_confirmation"
    DONE = "done"
    DISCARDED = "discarded"
    FAILED = "failed"


class IntentType(str, Enum):
    SCHEDULE_TOUCHPOINT = "schedule_touchpoint"
    CREATE_TASK = "create_task"
    CREATE_BO = "create_business_opportunity"
    ADD_LEAD = "add_lead"
    UNKNOWN = "unknown"


class InputMode(str, Enum):
    QUICK = "quick"
    EOD = "eod"
    OCR_SCAN = "ocr_scan"
