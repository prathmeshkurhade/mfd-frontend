// All values match backend enums.py exactly

export const LEAD_STATUS = [
  { value: 'follow_up', label: 'Follow Up' },
  { value: 'meeting_scheduled', label: 'Meeting Scheduled' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'converted', label: 'Converted' },
] as const

export const SOURCE_OPTIONS = [
  { value: 'natural_market', label: 'Natural Market' },
  { value: 'referral', label: 'Referral' },
  { value: 'social_networking', label: 'Social Networking' },
  { value: 'business_group', label: 'Business Group' },
  { value: 'marketing_activity', label: 'Marketing Activity' },
  { value: 'iap', label: 'IAP' },
  { value: 'cold_call', label: 'Cold Call' },
  { value: 'social_media', label: 'Social Media' },
] as const

export const GENDER_OPTIONS = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
] as const

export const MARITAL_STATUS_OPTIONS = [
  { value: 'single', label: 'Single' },
  { value: 'married', label: 'Married' },
  { value: 'divorced', label: 'Divorced' },
  { value: 'widower', label: 'Widower' },
  { value: 'separated', label: 'Separated' },
  { value: 'dont_know', label: "Don't Know" },
] as const

export const OCCUPATION_OPTIONS = [
  { value: 'service', label: 'Service' },
  { value: 'business', label: 'Business' },
  { value: 'retired', label: 'Retired' },
  { value: 'professional', label: 'Professional' },
  { value: 'student', label: 'Student' },
  { value: 'self_employed', label: 'Self Employed' },
  { value: 'housemaker', label: 'Housemaker' },
  { value: 'dont_know', label: "Don't Know" },
] as const

export const INCOME_GROUP_OPTIONS = [
  { value: 'zero', label: 'Zero' },
  { value: '1_to_2_5', label: '1-2.5 Lakhs' },
  { value: '2_6_to_8_8', label: '2.6-8.8 Lakhs' },
  { value: '8_9_to_12', label: '8.9-12 Lakhs' },
  { value: '12_1_to_24', label: '12.1-24 Lakhs' },
  { value: '24_1_to_48', label: '24.1-48 Lakhs' },
  { value: '48_1_plus', label: '48.1+ Lakhs' },
  { value: 'dont_know', label: "Don't Know" },
] as const

export const AGE_GROUP_OPTIONS = [
  { value: 'below_18', label: 'Below 18' },
  { value: '18_to_24', label: '18-24' },
  { value: '25_to_35', label: '25-35' },
  { value: '36_to_45', label: '36-45' },
  { value: '46_to_55', label: '46-55' },
  { value: '56_plus', label: '56+' },
  { value: 'dont_know', label: "Don't Know" },
] as const

export const RISK_PROFILE_OPTIONS = [
  { value: 'conservative', label: 'Conservative' },
  { value: 'moderately_conservative', label: 'Moderately Conservative' },
  { value: 'moderate', label: 'Moderate' },
  { value: 'moderately_aggressive', label: 'Moderately Aggressive' },
  { value: 'aggressive', label: 'Aggressive' },
] as const

export const TASK_STATUS = [
  { value: 'pending', label: 'Pending' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'carried_forward', label: 'Carried Forward' },
] as const

export const TASK_PRIORITY = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
] as const

export const TASK_MEDIUM = [
  { value: 'call', label: 'Call' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'email', label: 'Email' },
  { value: 'in_person', label: 'In Person' },
  { value: 'video_call', label: 'Video Call' },
] as const

export const TOUCHPOINT_STATUS = [
  { value: 'scheduled', label: 'Scheduled' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'rescheduled', label: 'Rescheduled' },
] as const

export const INTERACTION_TYPES = [
  { value: 'meeting_office', label: 'Meeting (Office)' },
  { value: 'meeting_home', label: 'Meeting (Home)' },
  { value: 'cafe', label: 'Cafe' },
  { value: 'restaurant', label: 'Restaurant' },
  { value: 'call', label: 'Call' },
  { value: 'video_call', label: 'Video Call' },
] as const

export const OPPORTUNITY_TYPES = [
  { value: 'sip', label: 'SIP' },
  { value: 'lumpsum', label: 'Lumpsum' },
  { value: 'swp', label: 'SWP' },
  { value: 'ncd', label: 'NCD' },
  { value: 'fd', label: 'FD' },
  { value: 'life_insurance', label: 'Life Insurance' },
  { value: 'health_insurance', label: 'Health Insurance' },
  { value: 'las', label: 'LAS' },
] as const

export const OPPORTUNITY_STAGES = [
  { value: 'identified', label: 'Identified' },
  { value: 'inbound', label: 'Inbound' },
  { value: 'proposed', label: 'Proposed' },
] as const

export const BO_OUTCOMES = [
  { value: 'open', label: 'Open' },
  { value: 'won', label: 'Won' },
  { value: 'lost', label: 'Lost' },
] as const

export const GOAL_TYPES = [
  { value: 'retirement', label: 'Retirement' },
  { value: 'child_education', label: 'Child Education' },
  { value: 'cash_surplus', label: 'Cash Surplus' },
  { value: 'lifestyle', label: 'Lifestyle' },
  { value: 'car_purchase', label: 'Car Purchase' },
  { value: 'bike_purchase', label: 'Bike Purchase' },
  { value: 'vacation', label: 'Vacation' },
  { value: 'wedding', label: 'Wedding' },
  { value: 'home_renovation', label: 'Home Renovation' },
  { value: 'emergency_fund', label: 'Emergency Fund' },
  { value: 'wealth_creation', label: 'Wealth Creation' },
  { value: 'gold_purchase', label: 'Gold Purchase' },
  { value: 'other', label: 'Other' },
] as const

export const GOAL_STATUS = [
  { value: 'active', label: 'Active' },
  { value: 'on_track', label: 'On Track' },
  { value: 'behind', label: 'Behind' },
  { value: 'achieved', label: 'Achieved' },
  { value: 'paused', label: 'Paused' },
] as const

export const PRODUCT_CATEGORIES = [
  { value: 'mutual_fund', label: 'Mutual Fund' },
  { value: 'stocks', label: 'Stocks' },
  { value: 'fixed_deposit', label: 'Fixed Deposit' },
  { value: 'recurring_deposit', label: 'Recurring Deposit' },
  { value: 'ppf', label: 'PPF' },
  { value: 'epf', label: 'EPF' },
  { value: 'nps', label: 'NPS' },
  { value: 'bonds', label: 'Bonds' },
  { value: 'ncd', label: 'NCD' },
  { value: 'gold', label: 'Gold' },
  { value: 'real_estate', label: 'Real Estate' },
  { value: 'term_insurance', label: 'Term Insurance' },
  { value: 'health_insurance', label: 'Health Insurance' },
  { value: 'pa_insurance', label: 'PA Insurance' },
  { value: 'life_insurance', label: 'Life Insurance' },
  { value: 'motor_insurance', label: 'Motor Insurance' },
  { value: 'ulip', label: 'ULIP' },
  { value: 'pms', label: 'PMS' },
  { value: 'aif', label: 'AIF' },
  { value: 'las', label: 'LAS' },
  { value: 'swp', label: 'SWP' },
  { value: 'other', label: 'Other' },
] as const

export const PRODUCT_STATUS = [
  { value: 'active', label: 'Active' },
  { value: 'paused', label: 'Paused' },
  { value: 'stopped', label: 'Stopped' },
  { value: 'redeemed', label: 'Redeemed' },
  { value: 'matured', label: 'Matured' },
  { value: 'lapsed', label: 'Lapsed' },
  { value: 'surrendered', label: 'Surrendered' },
] as const

export const INVESTMENT_TYPES = [
  { value: 'sip', label: 'SIP' },
  { value: 'lumpsum', label: 'Lumpsum' },
  { value: 'both', label: 'Both' },
] as const

export const TRANSACTION_TYPES = [
  { value: 'sip_installment', label: 'SIP Installment' },
  { value: 'additional_purchase', label: 'Additional Purchase' },
  { value: 'lumpsum', label: 'Lumpsum' },
  { value: 'redemption', label: 'Redemption' },
  { value: 'partial_redemption', label: 'Partial Redemption' },
  { value: 'switch_in', label: 'Switch In' },
  { value: 'switch_out', label: 'Switch Out' },
  { value: 'dividend', label: 'Dividend' },
  { value: 'premium_paid', label: 'Premium Paid' },
] as const

export const PREMIUM_FREQUENCY = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'half_yearly', label: 'Half Yearly' },
  { value: 'yearly', label: 'Yearly' },
  { value: 'one_time', label: 'One Time' },
] as const

export const CALCULATOR_TYPES = [
  { value: 'sip_lumpsum_goal', label: 'SIP/Lumpsum/Goal', icon: 'TrendingUp' },
  { value: 'vehicle', label: 'Vehicle', icon: 'Car' },
  { value: 'vacation', label: 'Vacation', icon: 'Plane' },
  { value: 'education', label: 'Education', icon: 'GraduationCap' },
  { value: 'wedding', label: 'Wedding', icon: 'Heart' },
  { value: 'gold', label: 'Gold', icon: 'Gem' },
  { value: 'retirement', label: 'Retirement', icon: 'Armchair' },
  { value: 'swp', label: 'SWP', icon: 'ArrowDownToLine' },
  { value: 'prepayment', label: 'Loan Prepayment', icon: 'CreditCard' },
  { value: 'cash_surplus', label: 'Cash Surplus', icon: 'Wallet' },
] as const

export const OPPORTUNITY_SOURCE_OPTIONS = [
  { value: 'goal_planning', label: 'Goal Planning' },
  { value: 'portfolio_rebalancing', label: 'Portfolio Rebalancing' },
  { value: 'client_servicing', label: 'Client Servicing' },
  { value: 'financial_activities', label: 'Financial Activities' },
] as const

export const CHANNEL_OPTIONS = [
  { value: 'email', label: 'Email' },
  { value: 'whatsapp', label: 'WhatsApp' },
] as const
