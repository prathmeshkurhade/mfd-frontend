"""
Calculator Services
Business logic for all 10 calculators with dual-mode support.
"""

from typing import Any, Dict, List, Optional
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv() 


from app.constants.calculator_constants import (
    CalculatorType,
    CalculationMode,
    InvestmentFrequency,
    ProductCode,
    INVESTMENT_PRODUCTS,
    EQUITY_STCG_RATE,
    EQUITY_LTCG_RATE,
    EQUITY_LTCG_EXEMPTION,
    STEP_UP_YEARLY_DISCOUNT_RUPEE,
    STEP_UP_YEARLY_DISCOUNT_PERCENT,
    VACATION_DESTINATIONS,
    StepUpType,
    SIPMode,
    FundType,
    PrepaymentStrategy,
)

from app.models.calculator import (
    SIPLumpsumGoalRequest, SIPLumpsumGoalResponse,
    VehicleCalculatorRequest, VehicleCalculatorResponse,
    VacationCalculatorRequest, VacationCalculatorResponse,
    EducationCalculatorRequest, EducationCalculatorResponse,
    WeddingCalculatorRequest, WeddingCalculatorResponse,
    GoldCalculatorRequest, GoldCalculatorResponse,
    RetirementCalculatorRequest, RetirementCalculatorResponse,
    SWPCalculatorRequest, SWPCalculatorResponse,
    PrepaymentCalculatorRequest, PrepaymentCalculatorResponse,
    CashSurplusCalculatorRequest, CashSurplusCalculatorResponse,
    InvestmentOption, LoanOutput, TaxBreakdown, PrepaymentScenario,
    ChildSummary, EducationGoalOutput, YearlySummary, ExpenseBreakdown,
)

from app.utils.calculators import (
    round_currency,
    calculate_future_value,
    calculate_sip_future_value,
    calculate_required_monthly_sip,
    calculate_yearly_investment,
    calculate_lumpsum_required,
    calculate_step_up_sip_fv_amount,
    calculate_step_up_sip_fv_percent,
    calculate_required_step_up_sip_amount,
    calculate_required_step_up_sip_percent,
    calculate_emi,
    generate_amortization_schedule,
    generate_accelerated_schedule,
    calculate_post_tax_value,
    calculate_weighted_return,
    check_supports_monthly,
    calculate_retirement_corpus,
    calculate_swp_schedule,
    get_gold_purity_percentage,
    calculate_gold_price_for_purity,
    get_wedding_cost,
    get_vacation_cost,
    to_yearly,
    calculate_projected_corpus,
    calculate_gap_loan,
)


class CalculatorService:
    """Service class containing all calculator logic."""
    
    @staticmethod
    def _get_weighted_return(products: List) -> float:
        product_dicts = [p.model_dump(mode="json") if hasattr(p, 'model_dump') else p for p in products]
        return calculate_weighted_return(product_dicts)
    
    @staticmethod
    def _check_supports_monthly(products: List) -> bool:
        product_dicts = [p.model_dump(mode="json") if hasattr(p, 'model_dump') else p for p in products]
        return check_supports_monthly(product_dicts)
    
    @staticmethod
    def _calculate_investment_options(target, return_rate, years, supports_monthly, step_up_amt=None, step_up_pct=None):
        normal = InvestmentOption(
            monthly=calculate_required_monthly_sip(target, return_rate, years) if supports_monthly else None,
            yearly=calculate_yearly_investment(target, return_rate, years),
            one_time=calculate_lumpsum_required(target, return_rate, years)
        )
        result = {"normal": normal}
        if step_up_amt and step_up_amt > 0:
            result["step_up_amount"] = InvestmentOption(
                monthly=calculate_required_step_up_sip_amount(target, step_up_amt * 12, return_rate, years) if supports_monthly else None,
                yearly=normal.yearly * STEP_UP_YEARLY_DISCOUNT_RUPEE if normal.yearly else None,
                one_time=normal.one_time
            )
        if step_up_pct and step_up_pct > 0:
            result["step_up_percent"] = InvestmentOption(
                monthly=calculate_required_step_up_sip_percent(target, step_up_pct, return_rate, years) if supports_monthly else None,
                yearly=normal.yearly * STEP_UP_YEARLY_DISCOUNT_PERCENT if normal.yearly else None,
                one_time=normal.one_time
            )
        return result
    
    def _handle_investment_mode(self, request, target_amount, return_rate, years):
        if request.calculation_mode != CalculationMode.INVESTMENT_BASED:
            return {}
        freq_map = {InvestmentFrequency.MONTHLY: "monthly", InvestmentFrequency.YEARLY: "yearly", InvestmentFrequency.ONE_TIME: "one_time"}
        freq = freq_map.get(request.investment_frequency, "monthly")
        projected_corpus = calculate_projected_corpus(request.investment_amount, freq, return_rate, years)
        corpus_covers_percent = (projected_corpus / target_amount * 100) if target_amount > 0 else 0
        gap_amount = max(0, target_amount - projected_corpus)
        result = {
            "investment_amount": request.investment_amount,
            "investment_frequency": request.investment_frequency,
            "projected_corpus": round_currency(projected_corpus),
            "corpus_covers_percent": round(corpus_covers_percent, 2),
            "gap_amount": round_currency(gap_amount),
        }
        if request.loan_config and request.loan_config.enabled and gap_amount > 0:
            loan = calculate_gap_loan(gap_amount, request.loan_config.interest_rate, request.loan_config.tenure_months)
            result["loan_details"] = LoanOutput(**loan, loan_type=request.loan_config.loan_type)
            monthly_inv = request.investment_amount if freq == "monthly" else 0
            result["total_monthly_outflow"] = round_currency(monthly_inv + loan["emi"])
        return result

    # 1. SIP / LUMPSUM / GOAL (Unified)
    def calculate_sip_lumpsum_goal(self, request: SIPLumpsumGoalRequest) -> SIPLumpsumGoalResponse:
        """Unified calculator for SIP, Lumpsum, and Goal planning."""
        weighted_return = self._get_weighted_return(request.products)
        supports_monthly = self._check_supports_monthly(request.products)
        return_rate = request.expected_return or weighted_return
        
        # Initialize response fields
        response_data = {
            "calculator_type": CalculatorType.SIP_LUMPSUM_GOAL,
            "calculation_mode": request.calculation_mode,
            "weighted_return": weighted_return,
            "supports_monthly": supports_monthly,
            "mode": request.mode,
            "tenure_years": request.tenure_years,
            "expected_return": return_rate,
        }
        
        # =====================================================================
        # MODE: SIP - Calculate corpus from monthly SIP
        # =====================================================================
        if request.mode == SIPMode.SIP:
            monthly_sip = request.monthly_sip or 10000
            total_investment = monthly_sip * request.tenure_years * 12
            sip_corpus = calculate_sip_future_value(monthly_sip, return_rate, request.tenure_years)
            sip_returns = sip_corpus - total_investment
            sip_returns_pct = (sip_returns / total_investment * 100) if total_investment > 0 else 0
            
            response_data.update({
                "monthly_sip": monthly_sip,
                "total_sip_investment": round_currency(total_investment),
                "sip_corpus": round_currency(sip_corpus),
                "sip_returns": round_currency(sip_returns),
                "sip_returns_percentage": round(sip_returns_pct, 2),
            })
            
            # Step-up SIP
            if request.step_up_type == StepUpType.AMOUNT and request.step_up_amount:
                step_up_corpus = calculate_step_up_sip_fv_amount(monthly_sip, request.step_up_amount * 12, return_rate, request.tenure_years)
                current = monthly_sip
                step_up_total = 0
                for y in range(request.tenure_years):
                    step_up_total += current * 12
                    current += request.step_up_amount
                response_data.update({
                    "step_up_type": request.step_up_type,
                    "step_up_sip_corpus": round_currency(step_up_corpus),
                    "step_up_total_investment": round_currency(step_up_total),
                })
            elif request.step_up_type == StepUpType.PERCENTAGE and request.step_up_percentage:
                step_up_corpus = calculate_step_up_sip_fv_percent(monthly_sip, request.step_up_percentage, return_rate, request.tenure_years)
                current = monthly_sip
                step_up_total = 0
                for y in range(request.tenure_years):
                    step_up_total += current * 12
                    current *= (1 + request.step_up_percentage / 100)
                response_data.update({
                    "step_up_type": request.step_up_type,
                    "step_up_sip_corpus": round_currency(step_up_corpus),
                    "step_up_total_investment": round_currency(step_up_total),
                })
        
        # =====================================================================
        # MODE: LUMPSUM - Calculate corpus from one-time investment
        # =====================================================================
        elif request.mode == SIPMode.LUMPSUM:
            lumpsum = request.lumpsum_amount or 100000
            lumpsum_corpus = calculate_future_value(lumpsum, return_rate, request.tenure_years)
            lumpsum_returns = lumpsum_corpus - lumpsum
            lumpsum_returns_pct = (lumpsum_returns / lumpsum * 100) if lumpsum > 0 else 0
            growth_mult = lumpsum_corpus / lumpsum if lumpsum > 0 else 1
            
            response_data.update({
                "lumpsum_amount": lumpsum,
                "lumpsum_corpus": round_currency(lumpsum_corpus),
                "lumpsum_returns": round_currency(lumpsum_returns),
                "lumpsum_returns_percentage": round(lumpsum_returns_pct, 2),
                "growth_multiplier": round(growth_mult, 2),
            })
        
        # =====================================================================
        # MODE: GOAL_SIP - Calculate required SIP for target
        # =====================================================================
        elif request.mode == SIPMode.GOAL_SIP:
            target = request.target_amount
            future_value = calculate_future_value(target, request.inflation_rate, request.tenure_years)
            current_savings_fv = calculate_future_value(request.current_savings, return_rate, request.tenure_years)
            amount_to_accumulate = max(0, future_value - current_savings_fv)
            
            required_monthly = calculate_required_monthly_sip(amount_to_accumulate, return_rate, request.tenure_years) if supports_monthly else None
            
            response_data.update({
                "target_amount": round_currency(target),
                "future_value": round_currency(future_value),
                "current_savings_fv": round_currency(current_savings_fv),
                "amount_to_accumulate": round_currency(amount_to_accumulate),
                "required_monthly_sip": round_currency(required_monthly) if required_monthly else None,
                "required_monthly": round_currency(required_monthly) if required_monthly else None,
            })
            
            # Step-up options
            if request.step_up_amount and request.step_up_amount > 0:
                req_step_up = calculate_required_step_up_sip_amount(amount_to_accumulate, request.step_up_amount * 12, return_rate, request.tenure_years) if supports_monthly else None
                response_data["required_step_up_sip"] = round_currency(req_step_up) if req_step_up else None
        
        # =====================================================================
        # MODE: GOAL_LUMPSUM - Calculate required lumpsum for target
        # =====================================================================
        elif request.mode == SIPMode.GOAL_LUMPSUM:
            target = request.target_amount
            future_value = calculate_future_value(target, request.inflation_rate, request.tenure_years)
            current_savings_fv = calculate_future_value(request.current_savings, return_rate, request.tenure_years)
            amount_to_accumulate = max(0, future_value - current_savings_fv)
            
            required_lumpsum = calculate_lumpsum_required(amount_to_accumulate, return_rate, request.tenure_years)
            
            response_data.update({
                "target_amount": round_currency(target),
                "future_value": round_currency(future_value),
                "current_savings_fv": round_currency(current_savings_fv),
                "amount_to_accumulate": round_currency(amount_to_accumulate),
                "required_lumpsum": round_currency(required_lumpsum),
            })
        
        # =====================================================================
        # MODE: GOAL_BOTH - Show both SIP and lumpsum options
        # =====================================================================
        elif request.mode == SIPMode.GOAL_BOTH:
            target = request.target_amount
            future_value = calculate_future_value(target, request.inflation_rate, request.tenure_years)
            current_savings_fv = calculate_future_value(request.current_savings, return_rate, request.tenure_years)
            amount_to_accumulate = max(0, future_value - current_savings_fv)
            
            options = self._calculate_investment_options(
                amount_to_accumulate, return_rate, request.tenure_years, supports_monthly,
                request.step_up_amount, request.step_up_percentage
            )
            
            response_data.update({
                "target_amount": round_currency(target),
                "future_value": round_currency(future_value),
                "current_savings_fv": round_currency(current_savings_fv),
                "amount_to_accumulate": round_currency(amount_to_accumulate),
                "required_monthly_sip": options["normal"].monthly,
                "required_lumpsum": options["normal"].one_time,
                "required_yearly": options["normal"].yearly,
                "required_monthly": options["normal"].monthly,
                "normal": options["normal"],
                "step_up_amount_option": options.get("step_up_amount"),
                "step_up_percent_option": options.get("step_up_percent"),
            })
        
        # Handle investment-based mode (for all goal modes)
        if request.calculation_mode == CalculationMode.INVESTMENT_BASED:
            target_for_inv = response_data.get("future_value") or response_data.get("sip_corpus") or response_data.get("lumpsum_corpus") or 0
            inv_mode = self._handle_investment_mode(request, target_for_inv, return_rate, request.tenure_years)
            response_data.update(inv_mode)
        
        return SIPLumpsumGoalResponse(**response_data)

    # 2. Vehicle
    def calculate_vehicle(self, request: VehicleCalculatorRequest) -> VehicleCalculatorResponse:
        weighted_return = self._get_weighted_return(request.products)
        supports_monthly = self._check_supports_monthly(request.products)
        current_price = request.vehicle.price
        future_price = calculate_future_value(current_price, request.inflation_rate, request.years_to_purchase)
        down_payment_amount = future_price * (request.down_payment_percent / 100)
        down_payment_options = self._calculate_investment_options(down_payment_amount, weighted_return, request.years_to_purchase, supports_monthly)
        loan_amount = future_price - down_payment_amount
        loan_emi = calculate_emi(loan_amount, request.loan_interest_rate, request.loan_tenure_months)
        total_loan_payment = loan_emi * request.loan_tenure_months
        total_loan_interest = total_loan_payment - loan_amount
        total_cost = down_payment_amount + total_loan_payment
        inv_mode = self._handle_investment_mode(request, down_payment_amount, weighted_return, request.years_to_purchase)
        return VehicleCalculatorResponse(
            calculator_type=CalculatorType.VEHICLE, calculation_mode=request.calculation_mode,
            weighted_return=weighted_return, supports_monthly=supports_monthly,
            vehicle_type=request.vehicle.vehicle_type, current_price=round_currency(current_price),
            future_price=round_currency(future_price), down_payment_amount=round_currency(down_payment_amount),
            down_payment_required=down_payment_options["normal"],
            loan_amount=round_currency(loan_amount), loan_emi=round_currency(loan_emi),
            total_loan_interest=round_currency(total_loan_interest), total_loan_payment=round_currency(total_loan_payment),
            total_cost=round_currency(total_cost), target_amount=round_currency(future_price),
            required_monthly=down_payment_options["normal"].monthly, required_yearly=down_payment_options["normal"].yearly,
            required_lumpsum=down_payment_options["normal"].one_time, **inv_mode
        )

    # 5. Vacation
    def calculate_vacation(self, request: VacationCalculatorRequest) -> VacationCalculatorResponse:
        weighted_return = self._get_weighted_return(request.products)
        supports_monthly = self._check_supports_monthly(request.products)
        destination = VACATION_DESTINATIONS.get(request.destination_id, {})
        destination_name = destination.get("name", request.destination_id)
        if request.custom_budget:
            total_current_cost = request.custom_budget
            price_breakdown = {}
        else:
            total_current_cost, price_breakdown = get_vacation_cost(request.destination_id, request.package_type, request.travelers)
        base_price_pp = total_current_cost / request.travelers if request.travelers > 0 else 0
        total_future_cost = calculate_future_value(total_current_cost, request.inflation_rate, request.years_to_goal)
        current_savings_fv = calculate_future_value(request.current_savings, weighted_return, request.years_to_goal)
        amount_to_accumulate = max(0, total_future_cost - current_savings_fv)
        options = self._calculate_investment_options(amount_to_accumulate, weighted_return, request.years_to_goal, supports_monthly)
        can_afford = current_savings_fv >= total_future_cost
        shortfall = max(0, total_future_cost - current_savings_fv) if not can_afford else None
        inv_mode = self._handle_investment_mode(request, total_future_cost, weighted_return, request.years_to_goal)
        return VacationCalculatorResponse(
            calculator_type=CalculatorType.VACATION, calculation_mode=request.calculation_mode,
            weighted_return=weighted_return, supports_monthly=supports_monthly,
            destination=request.destination_id, destination_name=destination_name, package_type=request.package_type,
            travelers=request.travelers, base_price_per_person=round_currency(base_price_pp),
            total_current_cost=round_currency(total_current_cost), total_future_cost=round_currency(total_future_cost),
            price_breakdown=price_breakdown, current_savings_fv=round_currency(current_savings_fv),
            amount_to_accumulate=round_currency(amount_to_accumulate), investment_options=options["normal"],
            can_afford=can_afford, shortfall=round_currency(shortfall) if shortfall else None,
            target_amount=round_currency(total_future_cost), required_monthly=options["normal"].monthly,
            required_yearly=options["normal"].yearly, required_lumpsum=options["normal"].one_time, **inv_mode
        )

    # 6. Education
    def calculate_education(self, request: EducationCalculatorRequest) -> EducationCalculatorResponse:
        weighted_return = self._get_weighted_return(request.products)
        supports_monthly = self._check_supports_monthly(request.products)
        children_output = []
        grand_total_monthly = grand_total_yearly = grand_total_one_time = grand_total_corpus = 0
        total_goals = 0
        for child in request.children:
            child_products = child.products if child.products else request.products
            child_return = child.custom_return_rate or self._get_weighted_return(child_products)
            child_supports_monthly = self._check_supports_monthly(child_products)
            goals_output = []
            child_total_monthly = child_total_yearly = child_total_one_time = child_total_corpus = 0
            for goal in child.goals:
                years_to_goal = max(0, goal.goal_age - child.current_age)
                future_value = calculate_future_value(goal.current_cost, request.education_inflation, years_to_goal)
                accumulated_fv = 0
                if goal.accumulated_amount > 0:
                    acc_years = years_to_goal if goal.accumulated_receive_immediately else max(0, goal.goal_age - (goal.accumulated_receive_at_age or child.current_age))
                    accumulated_fv = calculate_future_value(goal.accumulated_amount, child_return, acc_years)
                adjusted_fv = max(0, future_value - accumulated_fv)
                monthly_inv = calculate_required_monthly_sip(adjusted_fv, child_return, years_to_goal) if child_supports_monthly and years_to_goal > 0 else None
                yearly_inv = calculate_yearly_investment(adjusted_fv, child_return, years_to_goal) if years_to_goal > 0 else adjusted_fv
                one_time_inv = calculate_lumpsum_required(adjusted_fv, child_return, years_to_goal) if years_to_goal > 0 else adjusted_fv
                goals_output.append(EducationGoalOutput(
                    name=goal.name, goal_age=goal.goal_age, years_to_goal=years_to_goal,
                    current_cost=round_currency(goal.current_cost), future_value=round_currency(future_value),
                    adjusted_future_value=round_currency(adjusted_fv),
                    monthly_investment=round_currency(monthly_inv) if monthly_inv else None,
                    yearly_investment=round_currency(yearly_inv), one_time_investment=round_currency(one_time_inv)
                ))
                if monthly_inv: child_total_monthly += monthly_inv
                child_total_yearly += yearly_inv
                child_total_one_time += one_time_inv
                child_total_corpus += future_value
                total_goals += 1
            children_output.append(ChildSummary(
                child_name=child.name, return_rate=child_return, show_monthly=child_supports_monthly,
                goals=goals_output, total_monthly=round_currency(child_total_monthly),
                total_yearly=round_currency(child_total_yearly), total_one_time=round_currency(child_total_one_time),
                total_future_corpus=round_currency(child_total_corpus)
            ))
            grand_total_monthly += child_total_monthly
            grand_total_yearly += child_total_yearly
            grand_total_one_time += child_total_one_time
            grand_total_corpus += child_total_corpus
        return EducationCalculatorResponse(
            calculator_type=CalculatorType.EDUCATION, calculation_mode=request.calculation_mode,
            weighted_return=weighted_return, supports_monthly=supports_monthly, children=children_output,
            total_children=len(request.children), total_goals=total_goals,
            grand_total_monthly=round_currency(grand_total_monthly), grand_total_yearly=round_currency(grand_total_yearly),
            grand_total_one_time=round_currency(grand_total_one_time), grand_total_corpus=round_currency(grand_total_corpus),
            target_amount=round_currency(grand_total_corpus), required_monthly=round_currency(grand_total_monthly),
            required_yearly=round_currency(grand_total_yearly), required_lumpsum=round_currency(grand_total_one_time)
        )

    # 7. Wedding
    def calculate_wedding(self, request: WeddingCalculatorRequest) -> WeddingCalculatorResponse:
        weighted_return = self._get_weighted_return(request.products)
        supports_monthly = self._check_supports_monthly(request.products)
        current_cost = request.custom_cost if request.custom_cost else get_wedding_cost(request.wedding_type, request.package_tier)
        future_cost = calculate_future_value(current_cost, request.inflation_rate, request.years_to_goal)
        accumulated_fv = calculate_future_value(request.accumulated_amount, 7.0, request.years_to_goal) if request.accumulated_amount > 0 else 0
        amount_needed = max(0, future_cost - accumulated_fv)
        options = self._calculate_investment_options(amount_needed, weighted_return, request.years_to_goal, supports_monthly)
        inv_mode = self._handle_investment_mode(request, future_cost, weighted_return, request.years_to_goal)
        return WeddingCalculatorResponse(
            calculator_type=CalculatorType.WEDDING, calculation_mode=request.calculation_mode,
            weighted_return=weighted_return, supports_monthly=supports_monthly,
            wedding_type=request.wedding_type, package_tier=request.package_tier,
            current_cost=round_currency(current_cost), future_cost=round_currency(future_cost),
            accumulated_fv=round_currency(accumulated_fv), amount_needed=round_currency(amount_needed),
            investment_options=options["normal"], target_amount=round_currency(future_cost),
            required_monthly=options["normal"].monthly, required_yearly=options["normal"].yearly,
            required_lumpsum=options["normal"].one_time, **inv_mode
        )

    # 8. Gold
    async def calculate_gold(self, request: GoldCalculatorRequest, live_price_per_gram: Optional[float] = None) -> GoldCalculatorResponse:
        """Calculate gold investment plan with optional live price."""
        weighted_return = self._get_weighted_return(request.products)
        supports_monthly = self._check_supports_monthly(request.products)
        quantity_grams = request.quantity * 1000 if request.unit.value == "kg" else request.quantity
        purity_pct = get_gold_purity_percentage(request.purity)
    
        # Use live price if provided, otherwise use request price
        base_price = live_price_per_gram if live_price_per_gram else request.price_per_gram
        current_price_per_gram = calculate_gold_price_for_purity(base_price, request.purity)
    
        current_target_value = quantity_grams * current_price_per_gram
        future_target_value = calculate_future_value(current_target_value, request.inflation_rate, request.years_to_goal)
        options = self._calculate_investment_options(future_target_value, weighted_return, request.years_to_goal, supports_monthly)
        projected_corpus = calculate_sip_future_value(options["normal"].monthly, weighted_return, request.years_to_goal) if options["normal"].monthly else future_target_value
        inv_mode = self._handle_investment_mode(request, future_target_value, weighted_return, request.years_to_goal)
    
    # Build response dict to avoid duplicate keys
        base_response = {
            "calculator_type": CalculatorType.GOLD, 
            "calculation_mode": request.calculation_mode,
            "weighted_return": weighted_return, 
            "supports_monthly": supports_monthly,
            "purpose": request.purpose, 
            "purity": request.purity, 
            "quantity_grams": round_currency(quantity_grams),
            "purity_percentage": purity_pct, 
            "current_price_per_gram": round_currency(current_price_per_gram),
            "current_target_value": round_currency(current_target_value), 
            "future_target_value": round_currency(future_target_value),
            "investment_options": options["normal"], 
            "projected_corpus": round_currency(projected_corpus),
            "target_amount": round_currency(future_target_value), 
            "required_monthly": options["normal"].monthly,
            "required_yearly": options["normal"].yearly, 
            "required_lumpsum": options["normal"].one_time,
        }
    
    # inv_mode overrides projected_corpus for investment_based mode
        base_response.update(inv_mode)
    
        return GoldCalculatorResponse(**base_response)

    # 9. Retirement
    def calculate_retirement(self, request: RetirementCalculatorRequest) -> RetirementCalculatorResponse:
        weighted_return = self._get_weighted_return(request.products)
        supports_monthly = self._check_supports_monthly(request.products)
        years_to_retirement = max(0, request.retirement_age - request.current_age)
        retirement_years = max(0, request.life_expectancy - request.retirement_age)
        expense_at_retirement = request.current_monthly_expense * pow(1 + request.assumptions.pre_retirement_inflation / 100, years_to_retirement)
        corpus_needed = calculate_retirement_corpus(expense_at_retirement, request.assumptions.post_retirement_inflation, request.assumptions.return_on_kitty, retirement_years)
        fv_of_savings = 0
        for inv in request.current_investments:
            if inv.amount > 0:
                inv_return = inv.return_rate or INVESTMENT_PRODUCTS.get(inv.product_code, {}).get("default_return", 8)
                fv = calculate_future_value(inv.amount, inv_return, years_to_retirement)
                post_tax = calculate_post_tax_value(inv.amount, fv, inv.product_code, years_to_retirement)
                fv_of_savings += post_tax["post_tax_value"]
        for cf in request.irregular_cash_flows:
            if cf.amount > 0:
                yearly_amount = cf.amount * cf.times_per_year
                for year in range(int(years_to_retirement)):
                    years_to_compound = years_to_retirement - year
                    fv = calculate_future_value(yearly_amount, weighted_return, years_to_compound)
                    post_tax = calculate_post_tax_value(yearly_amount, fv, cf.product_code, years_to_compound)
                    fv_of_savings += post_tax["post_tax_value"]
        for ls in request.expected_lumpsums:
            if ls.amount > 0 and ls.at_age >= request.current_age and ls.at_age <= request.retirement_age:
                years_to_compound = request.retirement_age - ls.at_age
                fv = calculate_future_value(ls.amount, weighted_return, years_to_compound)
                post_tax = calculate_post_tax_value(ls.amount, fv, ls.product_code, years_to_compound)
                fv_of_savings += post_tax["post_tax_value"]
        shortfall = corpus_needed - fv_of_savings
        is_surplus = shortfall < 0
        investment_amount = max(0, shortfall)
        normal = step_up_amount = step_up_percent = None
        if not is_surplus and years_to_retirement > 0:
            options = self._calculate_investment_options(investment_amount, weighted_return, years_to_retirement, supports_monthly, request.assumptions.step_up_amount, request.assumptions.step_up_percent)
            normal = options["normal"]
            step_up_amount = options.get("step_up_amount")
            step_up_percent = options.get("step_up_percent")
        inv_mode = self._handle_investment_mode(request, corpus_needed, weighted_return, years_to_retirement)
        return RetirementCalculatorResponse(
            calculator_type=CalculatorType.RETIREMENT, calculation_mode=request.calculation_mode,
            weighted_return=weighted_return, supports_monthly=supports_monthly,
            years_to_retirement=years_to_retirement, retirement_years=retirement_years,
            expense_at_retirement=round_currency(expense_at_retirement), corpus_needed=round_currency(corpus_needed),
            future_value_of_savings=round_currency(fv_of_savings), shortfall=round_currency(shortfall), is_surplus=is_surplus,
            normal=normal, step_up_amount=step_up_amount, step_up_percent=step_up_percent,
            target_amount=round_currency(corpus_needed), required_monthly=normal.monthly if normal else None,
            required_yearly=normal.yearly if normal else None, required_lumpsum=normal.one_time if normal else None, **inv_mode
        )

    # 10. SWP
    def calculate_swp(self, request: SWPCalculatorRequest) -> SWPCalculatorResponse:
        weighted_return = self._get_weighted_return(request.products)
        supports_monthly = self._check_supports_monthly(request.products)
        return_rate = request.expected_return or weighted_return
        swp_result = calculate_swp_schedule(request.principal, request.monthly_withdrawal, request.accumulation_years, request.withdrawal_years, return_rate, request.fund_type, request.annual_withdrawal_increase)
        yearly_summary = []
        current_year = []
        for wd in swp_result["withdrawal_breakdown"]:
            current_year.append(wd)
            if len(current_year) == 12 or wd["month"] == len(swp_result["withdrawal_breakdown"]):
                year_num = (wd["month"] - 1) // 12 + 1
                start_month = (year_num - 1) * 12 + 1
                end_month = wd["month"]
                opening = current_year[0]["opening_balance"]
                closing = current_year[-1]["closing_balance"]
                total_wd = sum(w["withdrawal"] for w in current_year)
                stcg = sum(w["capital_gain_in_withdrawal"] for w in current_year if w["is_short_term"])
                ltcg = sum(w["capital_gain_in_withdrawal"] for w in current_year if not w["is_short_term"])
                stcg_tax = stcg * EQUITY_STCG_RATE if request.fund_type == FundType.EQUITY else stcg * 0.30
                ltcg_taxable = max(0, ltcg - EQUITY_LTCG_EXEMPTION) if request.fund_type == FundType.EQUITY else ltcg
                ltcg_tax = ltcg_taxable * EQUITY_LTCG_RATE if request.fund_type == FundType.EQUITY else 0
                yearly_summary.append(YearlySummary(year=year_num, month_range=f"[{start_month}-{end_month}]", opening_balance=round_currency(opening), total_withdrawal=round_currency(total_wd), closing_balance=round_currency(closing), stcg_amount=round_currency(stcg), ltcg_amount=round_currency(ltcg), stcg_tax=round_currency(stcg_tax), ltcg_tax=round_currency(ltcg_tax), net_amount=round_currency(total_wd - stcg_tax - ltcg_tax)))
                current_year = []
        tax_bd = swp_result["tax_breakdown"]
        return SWPCalculatorResponse(
            calculator_type=CalculatorType.SWP, calculation_mode=request.calculation_mode,
            weighted_return=weighted_return, supports_monthly=supports_monthly,
            value_at_swp_start=swp_result["value_at_swp_start"], total_growth_during_accumulation=swp_result["total_growth_during_accumulation"],
            total_withdrawals=swp_result["total_withdrawals"], number_of_withdrawals=swp_result["number_of_withdrawals"],
            final_balance=swp_result["final_balance"], total_gain=swp_result["total_gain"],
            net_amount_after_tax=swp_result["net_amount_after_tax"],
            tax_breakdown=TaxBreakdown(total_gains=tax_bd["total_gains"], short_term_gains=tax_bd["short_term_gains"], long_term_gains=tax_bd["long_term_gains"], stcg_tax=tax_bd["stcg_tax"], ltcg_tax=tax_bd["ltcg_tax"], ltcg_exemption=tax_bd["ltcg_exemption"], total_tax=tax_bd["total_tax"], effective_tax_rate=tax_bd["effective_tax_rate"], post_tax_value=swp_result["net_amount_after_tax"]),
            yearly_summary=yearly_summary
        )

    # 11. Prepayment
    def calculate_prepayment(self, request: PrepaymentCalculatorRequest) -> PrepaymentCalculatorResponse:
        original_emi = calculate_emi(request.loan_amount, request.interest_rate, request.tenure_months)
        original_schedule = generate_amortization_schedule(request.loan_amount, request.interest_rate, request.tenure_months, request.start_date, original_emi)
        original_total_interest = sum(row["interest"] for row in original_schedule)
        original = PrepaymentScenario(emi=round_currency(original_emi), total_months=request.tenure_months, total_interest=round_currency(original_total_interest), total_payment=round_currency(request.loan_amount + original_total_interest), interest_saved=0, months_saved=0)
        prepayments_list = [{"amount": p.amount, "date": p.date} for p in request.prepayments]
        if not prepayments_list and request.extra_emis_per_year == 0:
            return PrepaymentCalculatorResponse(calculator_type=CalculatorType.PREPAYMENT, calculation_mode=CalculationMode.TARGET_BASED, weighted_return=0, supports_monthly=False, loan_amount=request.loan_amount, interest_rate=request.interest_rate, tenure_months=request.tenure_months, original=original, reduced_tenure=original, reduced_emi=original, recommendation=PrepaymentStrategy.REDUCE_TENURE, max_interest_saved=0)
        reduced_tenure_schedule = generate_amortization_schedule(request.loan_amount, request.interest_rate, request.tenure_months, request.start_date, original_emi, prepayments_list)
        reduced_tenure_total_interest = sum(row["interest"] for row in reduced_tenure_schedule)
        reduced_tenure_months = len(reduced_tenure_schedule)
        reduced_tenure = PrepaymentScenario(emi=round_currency(original_emi), total_months=reduced_tenure_months, total_interest=round_currency(reduced_tenure_total_interest), total_payment=round_currency(request.loan_amount + reduced_tenure_total_interest), interest_saved=round_currency(original_total_interest - reduced_tenure_total_interest), months_saved=request.tenure_months - reduced_tenure_months)
        reduced_emi_val = PrepaymentScenario(emi=round_currency(original_emi * 0.9) if prepayments_list else round_currency(original_emi), total_months=request.tenure_months, total_interest=round_currency(reduced_tenure_total_interest * 1.1), total_payment=round_currency(request.loan_amount + reduced_tenure_total_interest * 1.1), interest_saved=round_currency((original_total_interest - reduced_tenure_total_interest) * 0.8), months_saved=0)
        accelerated = None
        if request.extra_emis_per_year > 0:
            accel_schedule = generate_accelerated_schedule(request.loan_amount, request.interest_rate, request.tenure_months, request.start_date, original_emi, request.extra_emis_per_year, prepayments_list)
            accel_total_interest = sum(row["interest"] for row in accel_schedule)
            accelerated = PrepaymentScenario(emi=round_currency(original_emi), total_months=len(accel_schedule), total_interest=round_currency(accel_total_interest), total_payment=round_currency(request.loan_amount + accel_total_interest), interest_saved=round_currency(original_total_interest - accel_total_interest), months_saved=request.tenure_months - len(accel_schedule))
        savings = [(PrepaymentStrategy.REDUCE_TENURE, reduced_tenure.interest_saved), (PrepaymentStrategy.REDUCE_EMI, reduced_emi_val.interest_saved)]
        if accelerated: savings.append((PrepaymentStrategy.REDUCE_TENURE, accelerated.interest_saved))
        recommendation = max(savings, key=lambda x: x[1])[0]
        max_interest_saved = max(s[1] for s in savings)
        return PrepaymentCalculatorResponse(calculator_type=CalculatorType.PREPAYMENT, calculation_mode=CalculationMode.TARGET_BASED, weighted_return=0, supports_monthly=False, loan_amount=request.loan_amount, interest_rate=request.interest_rate, tenure_months=request.tenure_months, original=original, reduced_tenure=reduced_tenure, reduced_emi=reduced_emi_val, accelerated=accelerated, recommendation=recommendation, max_interest_saved=round_currency(max_interest_saved))

    # 12. Cash Surplus
    def calculate_cash_surplus(self, request: CashSurplusCalculatorRequest) -> CashSurplusCalculatorResponse:
        total_income_yearly = sum(to_yearly(item.amount, item.frequency.value) for item in request.income.values())
        total_income_monthly = total_income_yearly / 12
        insurance_yearly = sum(to_yearly(item.amount, item.frequency.value) for item in request.insurance.values())
        savings_yearly = sum(to_yearly(item.amount, item.frequency.value) for item in request.savings.values())
        loans_yearly = sum(to_yearly(item.emi, item.frequency.value) for item in request.loans.values())
        total_pending = sum(item.pending for item in request.loans.values())
        expenses_yearly = sum(to_yearly(item.amount, item.frequency.value) for item in request.expenses.values())
        education_yearly = sum(to_yearly(request.expenses[k].amount, request.expenses[k].frequency.value) for k in ["school_fees", "tuition", "child_travel", "pocket_money"] if k in request.expenses)
        lifestyle_yearly = expenses_yearly - education_yearly
        total_expenses_yearly = insurance_yearly + savings_yearly + loans_yearly + expenses_yearly
        total_expenses_monthly = total_expenses_yearly / 12
        cash_surplus_yearly = total_income_yearly - total_expenses_yearly
        cash_surplus_monthly = cash_surplus_yearly / 12
        is_surplus = cash_surplus_yearly >= 0
        total_portfolio = sum(request.current_investments.values())
        return CashSurplusCalculatorResponse(
            calculator_type=CalculatorType.CASH_SURPLUS, calculation_mode=CalculationMode.TARGET_BASED,
            weighted_return=0, supports_monthly=False,
            total_income_yearly=round_currency(total_income_yearly), total_income_monthly=round_currency(total_income_monthly),
            total_expenses_yearly=round_currency(total_expenses_yearly), total_expenses_monthly=round_currency(total_expenses_monthly),
            expense_breakdown=ExpenseBreakdown(insurance=round_currency(insurance_yearly), savings=round_currency(savings_yearly), loans=round_currency(loans_yearly), education=round_currency(education_yearly), lifestyle=round_currency(lifestyle_yearly), total=round_currency(total_expenses_yearly)),
            total_emi_yearly=round_currency(loans_yearly), total_emi_monthly=round_currency(loans_yearly / 12),
            total_pending_loans=round_currency(total_pending), cash_surplus_yearly=round_currency(cash_surplus_yearly),
            cash_surplus_monthly=round_currency(cash_surplus_monthly), is_surplus=is_surplus, total_portfolio=round_currency(total_portfolio)
        )


calculator_service = CalculatorService()