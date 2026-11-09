"""
LLM-Compiled Rules Engine for Project A.
Concept: The LLM converts statutory rule text into a verified declarative rulebook (JSON schema / AST) ONCE.
Human reviews and approves the compiled artifact.
At query time, the compiled rulebook executes in pure deterministic Python with 0 LLM latency, 0 runtime cost, and 100% auditability.
"""

import json
from typing import Dict, Any, List, Tuple
from project_a.models import (
    TaxPayerProfile,
    DeductionBreakdown,
    TaxBreakdown,
    SlabDetail,
    RegimeComparison,
)


def round_to_10(val: float) -> float:
    return float(round(val / 10.0) * 10)


COMPILED_RULES_FY24_25 = {
    "version": "FY2024-25_v1.0",
    "reviewed_by": "Tax Lead & Compliance Engineer",
    "financial_year": "2024-25",
    "old_regime": {
        "standard_deduction": {"cap": 50000.0, "section": "16(ia)"},
        "hra": {
            "section": "10(13A)",
            "rule": "2A",
            "metro_multiplier": 0.50,
            "non_metro_multiplier": 0.40,
            "rent_excess_multiplier": 0.10,
        },
        "section_80c": {"cap": 150000.0, "section": "80C"},
        "section_80ccd_1b": {"cap": 50000.0, "section": "80CCD(1B)"},
        "section_80d": {
            "section": "80D",
            "self_under_60": 25000.0,
            "self_senior": 50000.0,
            "parents_non_senior": 25000.0,
            "parents_senior": 50000.0,
        },
        "section_24b": {"cap": 200000.0, "section": "24(b)"},
        "slabs": {
            "general": [
                {"low": 0.0, "high": 250000.0, "rate": 0.0, "label": "0 - 2.5L @ 0%"},
                {"low": 250000.0, "high": 500000.0, "rate": 0.05, "label": "2.5L - 5L @ 5%"},
                {"low": 500000.0, "high": 1000000.0, "rate": 0.20, "label": "5L - 10L @ 20%"},
                {"low": 1000000.0, "high": None, "rate": 0.30, "label": "> 10L @ 30%"},
            ],
            "senior": [
                {"low": 0.0, "high": 300000.0, "rate": 0.0, "label": "0 - 3L @ 0%"},
                {"low": 300000.0, "high": 500000.0, "rate": 0.05, "label": "3L - 5L @ 5%"},
                {"low": 500000.0, "high": 1000000.0, "rate": 0.20, "label": "5L - 10L @ 20%"},
                {"low": 1000000.0, "high": None, "rate": 0.30, "label": "> 10L @ 30%"},
            ],
            "super_senior": [
                {"low": 0.0, "high": 500000.0, "rate": 0.0, "label": "0 - 5L @ 0%"},
                {"low": 500000.0, "high": 1000000.0, "rate": 0.20, "label": "5L - 10L @ 20%"},
                {"low": 1000000.0, "high": None, "rate": 0.30, "label": "> 10L @ 30%"},
            ],
        },
        "rebate_87a": {"threshold": 500000.0, "max_amount": 12500.0, "marginal_relief": False},
        "surcharges": [
            {"threshold": 5000000.0, "rate": 0.10, "prev_rate": 0.0},
            {"threshold": 10000000.0, "rate": 0.15, "prev_rate": 0.10},
            {"threshold": 20000000.0, "rate": 0.25, "prev_rate": 0.15},
            {"threshold": 50000000.0, "rate": 0.37, "prev_rate": 0.25},
        ],
    },
    "new_regime": {
        "standard_deduction": {"cap": 75000.0, "section": "115BAC(1A)"},
        "slabs": [
            {"low": 0.0, "high": 300000.0, "rate": 0.0, "label": "0 - 3L @ 0%"},
            {"low": 300000.0, "high": 700000.0, "rate": 0.05, "label": "3L - 7L @ 5%"},
            {"low": 700000.0, "high": 1000000.0, "rate": 0.10, "label": "7L - 10L @ 10%"},
            {"low": 1000000.0, "high": 1200000.0, "rate": 0.15, "label": "10L - 12L @ 15%"},
            {"low": 1200000.0, "high": 1500000.0, "rate": 0.20, "label": "12L - 15L @ 20%"},
            {"low": 1500000.0, "high": None, "rate": 0.30, "label": "> 15L @ 30%"},
        ],
        "rebate_87a": {"threshold": 700000.0, "max_amount": 25000.0, "marginal_relief": True},
        "surcharges": [
            {"threshold": 5000000.0, "rate": 0.10, "prev_rate": 0.0},
            {"threshold": 10000000.0, "rate": 0.15, "prev_rate": 0.10},
            {"threshold": 20000000.0, "rate": 0.25, "prev_rate": 0.15},
        ],
    },
    "cess": {"rate": 0.04, "section": "Finance Act Health & Education Cess"},
}

COMPILED_RULES_FY25_26 = {
    "version": "FY2025-26_v1.0",
    "reviewed_by": "Tax Lead & Compliance Engineer",
    "financial_year": "2025-26",
    "old_regime": COMPILED_RULES_FY24_25["old_regime"],  # Old regime remains unchanged in Budget 2025
    "new_regime": {
        "standard_deduction": {"cap": 75000.0, "section": "115BAC"},
        "slabs": [
            {"low": 0.0, "high": 400000.0, "rate": 0.0, "label": "0 - 4L @ 0%"},
            {"low": 400000.0, "high": 800000.0, "rate": 0.05, "label": "4L - 8L @ 5%"},
            {"low": 800000.0, "high": 1200000.0, "rate": 0.10, "label": "8L - 12L @ 10%"},
            {"low": 1200000.0, "high": 1600000.0, "rate": 0.15, "label": "12L - 16L @ 15%"},
            {"low": 1600000.0, "high": 2000000.0, "rate": 0.20, "label": "16L - 20L @ 20%"},
            {"low": 2000000.0, "high": 2400000.0, "rate": 0.25, "label": "20L - 24L @ 25%"},
            {"low": 2400000.0, "high": None, "rate": 0.30, "label": "> 24L @ 30%"},
        ],
        "rebate_87a": {"threshold": 1200000.0, "max_amount": 60000.0, "marginal_relief": True},
        "surcharges": [
            {"threshold": 5000000.0, "rate": 0.10, "prev_rate": 0.0},
            {"threshold": 10000000.0, "rate": 0.15, "prev_rate": 0.10},
            {"threshold": 20000000.0, "rate": 0.25, "prev_rate": 0.15},
        ],
    },
    "cess": {"rate": 0.04, "section": "Finance Act Health & Education Cess"},
}


class CompiledRulesInterpreter:
    """
    Executes compiled statutory rules.
    Runs in sub-millisecond time with zero external API calls.
    """

    def __init__(self, ruleset: Dict[str, Any]):
        self.rules = ruleset
        self.fy = ruleset["financial_year"]

    def _eval_slabs(self, income: float, slab_def: List[Dict[str, Any]]) -> Tuple[float, List[SlabDetail]]:
        base_tax = 0.0
        details = []
        for slab in slab_def:
            low = slab["low"]
            high = slab["high"]
            rate = slab["rate"]
            label = slab["label"]
            if income > low:
                taxable_amount = (min(income, high) - low) if high is not None else (income - low)
                tax_amt = taxable_amount * rate
                base_tax += tax_amt
                details.append(
                    SlabDetail(
                        rate=rate,
                        min_income=low,
                        max_income=high,
                        taxable_amount_in_slab=taxable_amount,
                        tax=tax_amt,
                        clause=label,
                    )
                )
        return base_tax, details

    def calculate_old(self, profile: TaxPayerProfile) -> TaxBreakdown:
        rules = self.rules["old_regime"]
        audit = [f"--- LLM-COMPILED OLD REGIME ({self.fy}) ---"]

        # Standard deduction
        std_ded = min(rules["standard_deduction"]["cap"], profile.gross_salary)
        audit.append(f"Section {rules['standard_deduction']['section']}: Standard Deduction = ₹{std_ded:,.0f}")

        # HRA Exemption
        hra_exemption = 0.0
        if profile.rent_paid > 0 and profile.hra_received > 0:
            basic = profile.basic_salary or (profile.gross_salary * 0.5)
            excess = max(0.0, profile.rent_paid - (rules["hra"]["rent_excess_multiplier"] * basic))
            mult = rules["hra"]["metro_multiplier"] if profile.is_metro else rules["hra"]["non_metro_multiplier"]
            salary_cap = mult * basic
            hra_exemption = min(profile.hra_received, excess, salary_cap)
            audit.append(f"Section 10(13A): HRA Exemption = ₹{hra_exemption:,.0f}")

        # 80C
        sec_80c = min(rules["section_80c"]["cap"], profile.section_80c)
        # 80CCD(1B)
        sec_80ccd_1b = min(rules["section_80ccd_1b"]["cap"], profile.section_80ccd_1b)
        # 80D
        d_cfg = rules["section_80d"]
        self_cap = d_cfg["self_senior"] if profile.age >= 60 else d_cfg["self_under_60"]
        par_cap = d_cfg["parents_senior"] if profile.parents_senior else d_cfg["parents_non_senior"]
        sec_80d = min(self_cap, profile.section_80d_self) + min(par_cap, profile.section_80d_parents)
        # 24b
        sec_24b = min(rules["section_24b"]["cap"], profile.home_loan_interest_self_occupied)

        total_deductions = std_ded + hra_exemption + sec_80c + sec_80ccd_1b + sec_80d + sec_24b
        audit.append(f"Compiled Total Deductions = ₹{total_deductions:,.0f}")

        ded_breakdown = DeductionBreakdown(
            standard_deduction=std_ded,
            hra_exemption=hra_exemption,
            sec_80c=sec_80c,
            sec_80ccd_1b=sec_80ccd_1b,
            sec_80d=sec_80d,
            sec_24b=sec_24b,
            total_deductions=total_deductions,
            audit_trail=audit.copy(),
        )

        taxable_raw = max(0.0, profile.gross_salary - total_deductions)
        net_taxable = round_to_10(taxable_raw)

        # Slab selection
        if profile.age >= 80:
            slab_def = rules["slabs"]["super_senior"]
        elif profile.age >= 60:
            slab_def = rules["slabs"]["senior"]
        else:
            slab_def = rules["slabs"]["general"]

        base_tax, slabs = self._eval_slabs(net_taxable, slab_def)

        # 87A
        rebate_cfg = rules["rebate_87a"]
        rebate_87a = 0.0
        if net_taxable <= rebate_cfg["threshold"]:
            rebate_87a = min(base_tax, rebate_cfg["max_amount"])
        tax_after_rebate = max(0.0, base_tax - rebate_87a)

        # Surcharges
        net_surcharge, surcharge_rate, raw_surcharge, marginal_relief = self._calc_surcharge(
            net_taxable, tax_after_rebate, rules["surcharges"], slab_def
        )

        tax_after_surcharge = tax_after_rebate + net_surcharge
        cess = tax_after_surcharge * self.rules["cess"]["rate"]
        total_tax = round_to_10(tax_after_surcharge + cess)

        return TaxBreakdown(
            regime="OLD",
            financial_year=self.fy,
            gross_income=profile.gross_salary,
            deductions=ded_breakdown,
            net_taxable_income=net_taxable,
            base_tax=base_tax,
            slab_details=slabs,
            rebate_87a=rebate_87a,
            rebate_87a_marginal_relief=0.0,
            tax_after_rebate=tax_after_rebate,
            surcharge_rate=surcharge_rate,
            surcharge_raw=raw_surcharge,
            surcharge_marginal_relief=marginal_relief,
            net_surcharge=net_surcharge,
            cess_4_pct=cess,
            total_tax_payable=total_tax,
            clause_audit_trail=audit,
        )

    def calculate_new(self, profile: TaxPayerProfile) -> TaxBreakdown:
        rules = self.rules["new_regime"]
        audit = [f"--- LLM-COMPILED NEW REGIME ({self.fy}) ---"]

        std_ded = min(rules["standard_deduction"]["cap"], profile.gross_salary)
        ded_breakdown = DeductionBreakdown(
            standard_deduction=std_ded,
            hra_exemption=0.0,
            sec_80c=0.0,
            sec_80ccd_1b=0.0,
            sec_80d=0.0,
            sec_24b=0.0,
            total_deductions=std_ded,
            audit_trail=[f"Standard deduction Section 115BAC: ₹{std_ded:,.0f}"],
        )

        taxable_raw = max(0.0, profile.gross_salary - std_ded)
        net_taxable = round_to_10(taxable_raw)

        base_tax, slabs = self._eval_slabs(net_taxable, rules["slabs"])

        # 87A rebate & marginal relief
        rebate_cfg = rules["rebate_87a"]
        rebate_87a = 0.0
        marginal_relief_87a = 0.0
        tax_after_rebate = base_tax

        if net_taxable <= rebate_cfg["threshold"]:
            rebate_87a = min(base_tax, rebate_cfg["max_amount"])
            tax_after_rebate = 0.0
        else:
            if rebate_cfg.get("marginal_relief"):
                excess = net_taxable - rebate_cfg["threshold"]
                if base_tax > excess:
                    marginal_relief_87a = base_tax - excess
                    tax_after_rebate = excess

        # Surcharge
        net_surcharge, surcharge_rate, raw_surcharge, marginal_relief = self._calc_surcharge(
            net_taxable, tax_after_rebate, rules["surcharges"], rules["slabs"]
        )

        tax_after_surcharge = tax_after_rebate + net_surcharge
        cess = tax_after_surcharge * self.rules["cess"]["rate"]
        total_tax = round_to_10(tax_after_surcharge + cess)

        return TaxBreakdown(
            regime="NEW",
            financial_year=self.fy,
            gross_income=profile.gross_salary,
            deductions=ded_breakdown,
            net_taxable_income=net_taxable,
            base_tax=base_tax,
            slab_details=slabs,
            rebate_87a=rebate_87a,
            rebate_87a_marginal_relief=marginal_relief_87a,
            tax_after_rebate=tax_after_rebate,
            surcharge_rate=surcharge_rate,
            surcharge_raw=raw_surcharge,
            surcharge_marginal_relief=marginal_relief,
            net_surcharge=net_surcharge,
            cess_4_pct=cess,
            total_tax_payable=total_tax,
            clause_audit_trail=audit,
        )

    def _calc_surcharge(
        self, income: float, base_tax: float, surcharge_defs: List[Dict[str, Any]], slab_def: List[Dict[str, Any]]
    ) -> Tuple[float, float, float, float]:
        if income <= 5000000.0:
            return 0.0, 0.0, 0.0, 0.0

        applicable_tier = None
        for tier in sorted(surcharge_defs, key=lambda x: x["threshold"]):
            if income > tier["threshold"]:
                applicable_tier = tier

        if not applicable_tier:
            return 0.0, 0.0, 0.0, 0.0

        rate = applicable_tier["rate"]
        thresh = applicable_tier["threshold"]
        prev_rate = applicable_tier["prev_rate"]

        raw_surcharge = base_tax * rate
        tax_at_thresh, _ = self._eval_slabs(thresh, slab_def)
        sur_at_thresh = tax_at_thresh * prev_rate
        cap = tax_at_thresh + sur_at_thresh + (income - thresh)

        total_with_sur = base_tax + raw_surcharge
        marginal_relief = max(0.0, total_with_sur - cap)
        net_sur = max(0.0, raw_surcharge - marginal_relief)

        return net_sur, rate, raw_surcharge, marginal_relief

    def compare_regimes(self, profile: TaxPayerProfile) -> RegimeComparison:
        old_res = self.calculate_old(profile)
        new_res = self.calculate_new(profile)
        diff = abs(old_res.total_tax_payable - new_res.total_tax_payable)
        if old_res.total_tax_payable < new_res.total_tax_payable:
            rec = "OLD"
            exp = f"Compiled rules show Old Regime saves ₹{diff:,.0f} due to total deductions."
        elif new_res.total_tax_payable < old_res.total_tax_payable:
            rec = "NEW"
            exp = f"Compiled rules show New Regime saves ₹{diff:,.0f} due to lower slab rates."
        else:
            rec = "EITHER"
            exp = "Both regimes yield identical tax liability."

        return RegimeComparison(
            financial_year=self.fy,
            old_regime=old_res,
            new_regime=new_res,
            recommended_regime=rec,
            tax_difference=diff,
            explanation=exp,
        )
