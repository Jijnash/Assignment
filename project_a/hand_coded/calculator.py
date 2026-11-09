"""
Hand-coded deterministic statutory rules engine for Indian Income Tax.
Supports both FY 2024-25 (AY 2025-26) and FY 2025-26 (AY 2026-27).
Provides rupee-exact calculations with a complete statutory clause audit trail.
"""

from typing import Tuple, List, Dict, Any, Optional
import math
from project_a.models import (
    TaxPayerProfile,
    DeductionBreakdown,
    TaxBreakdown,
    SlabDetail,
    RegimeComparison,
)


def round_to_10(val: float) -> float:
    """Section 288A & Section 288B rounding to nearest multiple of 10."""
    return float(round(val / 10.0) * 10)


class HandCodedTaxCalculator:
    """
    Deterministic rule-based tax engine.
    Encodes Indian Income-tax provisions with exact statutory clause attribution.
    """

    def __init__(self, financial_year: str = "2024-25"):
        if financial_year not in ["2024-25", "2025-26"]:
            raise ValueError(f"Unsupported financial year: {financial_year}. Must be '2024-25' or '2025-26'.")
        self.fy = financial_year

    def compute_hra_exemption(self, profile: TaxPayerProfile) -> Tuple[float, List[str]]:
        """
        Computes Section 10(13A) read with Rule 2A exemption for HRA.
        Only applicable under Old Regime.
        """
        audit = []
        if profile.rent_paid <= 0 or profile.hra_received <= 0:
            audit.append("Section 10(13A): No rent paid or no HRA received -> HRA Exemption = ₹0")
            return 0.0, audit

        basic = profile.basic_salary or (profile.gross_salary * 0.5)
        excess_rent = max(0.0, profile.rent_paid - (0.10 * basic))
        metro_cap = 0.50 if profile.is_metro else 0.40
        metro_pct_text = "50%" if profile.is_metro else "40%"
        salary_limit = metro_cap * basic

        exemption = min(profile.hra_received, excess_rent, salary_limit)
        audit.append(
            f"Section 10(13A) / Rule 2A: Least of [Actual HRA: ₹{profile.hra_received:,.0f}, "
            f"Rent - 10% Basic: ₹{excess_rent:,.0f}, {metro_pct_text} Basic: ₹{salary_limit:,.0f}] = ₹{exemption:,.0f}"
        )
        return float(exemption), audit

    def compute_deductions_old_regime(self, profile: TaxPayerProfile) -> DeductionBreakdown:
        """
        Computes all allowable deductions under Old Regime:
        - Section 16(ia): Standard Deduction
        - Section 10(13A): HRA
        - Section 80C: Investments up to ₹1,50,000
        - Section 80CCD(1B): NPS up to ₹50,000
        - Section 80D: Health insurance (Self & Parents, senior citizen limits)
        - Section 24(b): Self-occupied housing loan interest up to ₹2,00,000
        """
        audit = []
        # Standard deduction: ₹50,000 under Old Regime for both FYs
        std_ded = min(50000.0, profile.gross_salary)
        audit.append(f"Section 16(ia): Standard Deduction = ₹{std_ded:,.0f}")

        # HRA Exemption
        hra_exemption, hra_audit = self.compute_hra_exemption(profile)
        audit.extend(hra_audit)

        # Section 80C
        sec_80c = min(150000.0, profile.section_80c)
        if profile.section_80c > 0:
            audit.append(f"Section 80C: Claimed ₹{profile.section_80c:,.0f}, Capped at ₹{sec_80c:,.0f}")

        # Section 80CCD(1B)
        sec_80ccd_1b = min(50000.0, profile.section_80ccd_1b)
        if profile.section_80ccd_1b > 0:
            audit.append(f"Section 80CCD(1B): NPS Additional Deduction = ₹{sec_80ccd_1b:,.0f}")

        # Section 80D
        self_limit = 50000.0 if profile.age >= 60 else 25000.0
        parent_limit = 50000.0 if profile.parents_senior else 25000.0
        sec_80d_self = min(self_limit, profile.section_80d_self)
        sec_80d_parents = min(parent_limit, profile.section_80d_parents)
        sec_80d_total = sec_80d_self + sec_80d_parents
        if sec_80d_total > 0:
            audit.append(
                f"Section 80D: Self/Family (limit ₹{self_limit:,.0f}) = ₹{sec_80d_self:,.0f}, "
                f"Parents (limit ₹{parent_limit:,.0f}) = ₹{sec_80d_parents:,.0f} -> Total = ₹{sec_80d_total:,.0f}"
            )

        # Section 24(b)
        sec_24b = min(200000.0, profile.home_loan_interest_self_occupied)
        if profile.home_loan_interest_self_occupied > 0:
            audit.append(
                f"Section 24(b): Self-occupied housing loan interest claimed ₹{profile.home_loan_interest_self_occupied:,.0f}, "
                f"Capped at ₹{sec_24b:,.0f}"
            )

        total = std_ded + hra_exemption + sec_80c + sec_80ccd_1b + sec_80d_total + sec_24b
        audit.append(f"Total Old Regime Deductions = ₹{total:,.0f}")

        return DeductionBreakdown(
            standard_deduction=std_ded,
            hra_exemption=hra_exemption,
            sec_80c=sec_80c,
            sec_80ccd_1b=sec_80ccd_1b,
            sec_80d=sec_80d_total,
            sec_24b=sec_24b,
            total_deductions=total,
            audit_trail=audit,
        )

    def compute_deductions_new_regime(self, profile: TaxPayerProfile) -> DeductionBreakdown:
        """
        Under New Regime (Section 115BAC):
        - Standard deduction is ₹75,000 for salaried employees (for both FY 2024-25 and FY 2025-26).
        - No Chapter VI-A deductions (80C, 80D, 80CCD(1B)), no HRA (10(13A)), no Sec 24(b) for self-occupied.
        """
        audit = []
        std_ded_limit = 75000.0
        std_ded = min(std_ded_limit, profile.gross_salary)
        audit.append(f"Section 115BAC(1A) read with Section 16(ia): Standard Deduction = ₹{std_ded:,.0f}")
        if profile.section_80c > 0 or profile.hra_received > 0 or profile.section_80d_self > 0 or profile.home_loan_interest_self_occupied > 0:
            audit.append("Section 115BAC(2): HRA, 80C, 80D, 80CCD(1B), and Sec 24(b) disallowable under New Regime.")

        return DeductionBreakdown(
            standard_deduction=std_ded,
            hra_exemption=0.0,
            sec_80c=0.0,
            sec_80ccd_1b=0.0,
            sec_80d=0.0,
            sec_24b=0.0,
            total_deductions=std_ded,
            audit_trail=audit,
        )

    def _compute_base_tax_old_regime(self, taxable_income: float, age: int) -> Tuple[float, List[SlabDetail]]:
        """
        Computes slab tax under Old Regime based on age brackets:
        - General (<60): Exemption ₹2,50,000
        - Senior Citizen (60-79): Exemption ₹3,00,000
        - Super Senior Citizen (80+): Exemption ₹5,00,000
        """
        slabs = []
        if age >= 80:
            thresholds = [
                (0.0, 500000.0, 0.0, "Old Regime Super Senior: Up to ₹5,00,000 @ 0%"),
                (500000.0, 1000000.0, 0.20, "Old Regime: ₹5,00,001 to ₹10,00,000 @ 20%"),
                (1000000.0, None, 0.30, "Old Regime: Above ₹10,00,000 @ 30%"),
            ]
        elif age >= 60:
            thresholds = [
                (0.0, 300000.0, 0.0, "Old Regime Senior: Up to ₹3,00,000 @ 0%"),
                (300000.0, 500000.0, 0.05, "Old Regime: ₹3,00,001 to ₹5,00,000 @ 5%"),
                (500000.0, 1000000.0, 0.20, "Old Regime: ₹5,00,001 to ₹10,00,000 @ 20%"),
                (1000000.0, None, 0.30, "Old Regime: Above ₹10,00,000 @ 30%"),
            ]
        else:
            thresholds = [
                (0.0, 250000.0, 0.0, "Old Regime: Up to ₹2,50,000 @ 0%"),
                (250000.0, 500000.0, 0.05, "Old Regime: ₹2,50,001 to ₹5,00,000 @ 5%"),
                (500000.0, 1000000.0, 0.20, "Old Regime: ₹5,00,001 to ₹10,00,000 @ 20%"),
                (1000000.0, None, 0.30, "Old Regime: Above ₹10,00,000 @ 30%"),
            ]

        total_tax = 0.0
        for low, high, rate, clause in thresholds:
            if taxable_income > low:
                taxable_in_slab = (min(taxable_income, high) - low) if high is not None else (taxable_income - low)
                tax_in_slab = taxable_in_slab * rate
                total_tax += tax_in_slab
                slabs.append(
                    SlabDetail(
                        rate=rate,
                        min_income=low,
                        max_income=high,
                        taxable_amount_in_slab=taxable_in_slab,
                        tax=tax_in_slab,
                        clause=clause,
                    )
                )
        return total_tax, slabs

    def _compute_base_tax_new_regime_24_25(self, taxable_income: float) -> Tuple[float, List[SlabDetail]]:
        """
        New Tax Regime Slabs for FY 2024-25 (Finance Act 2024):
        - 0 to ₹3,00,000: Nil
        - ₹3,00,001 to ₹7,00,000: 5%
        - ₹7,00,001 to ₹10,00,000: 10%
        - ₹10,00,001 to ₹12,00,000: 15%
        - ₹12,00,001 to ₹15,00,000: 20%
        - Above ₹15,00,000: 30%
        """
        thresholds = [
            (0.0, 300000.0, 0.0, "Section 115BAC(1A): Up to ₹3,00,000 @ 0%"),
            (300000.0, 700000.0, 0.05, "Section 115BAC(1A): ₹3,00,001 to ₹7,00,000 @ 5%"),
            (700000.0, 1000000.0, 0.10, "Section 115BAC(1A): ₹7,00,001 to ₹10,00,000 @ 10%"),
            (1000000.0, 1200000.0, 0.15, "Section 115BAC(1A): ₹10,00,001 to ₹12,00,000 @ 15%"),
            (1200000.0, 1500000.0, 0.20, "Section 115BAC(1A): ₹12,00,001 to ₹15,00,000 @ 20%"),
            (1500000.0, None, 0.30, "Section 115BAC(1A): Above ₹15,00,000 @ 30%"),
        ]
        total_tax = 0.0
        slabs = []
        for low, high, rate, clause in thresholds:
            if taxable_income > low:
                taxable_in_slab = (min(taxable_income, high) - low) if high is not None else (taxable_income - low)
                tax_in_slab = taxable_in_slab * rate
                total_tax += tax_in_slab
                slabs.append(
                    SlabDetail(
                        rate=rate,
                        min_income=low,
                        max_income=high,
                        taxable_amount_in_slab=taxable_in_slab,
                        tax=tax_in_slab,
                        clause=clause,
                    )
                )
        return total_tax, slabs

    def _compute_base_tax_new_regime_25_26(self, taxable_income: float) -> Tuple[float, List[SlabDetail]]:
        """
        New Tax Regime Slabs for FY 2025-26 (Finance Act 2025):
        - Up to ₹4,00,000: Nil
        - ₹4,00,001 to ₹8,00,000: 5%
        - ₹8,00,001 to ₹12,00,000: 10%
        - ₹12,00,001 to ₹16,00,000: 15%
        - ₹16,00,001 to ₹20,00,000: 20%
        - ₹20,00,001 to ₹24,00,000: 25%
        - Above ₹24,00,000: 30%
        """
        thresholds = [
            (0.0, 400000.0, 0.0, "Section 115BAC (Finance Act 2025): Up to ₹4,00,000 @ 0%"),
            (400000.0, 800000.0, 0.05, "Section 115BAC (Finance Act 2025): ₹4,00,001 to ₹8,00,000 @ 5%"),
            (800000.0, 1200000.0, 0.10, "Section 115BAC (Finance Act 2025): ₹8,00,001 to ₹12,00,000 @ 10%"),
            (1200000.0, 1600000.0, 0.15, "Section 115BAC (Finance Act 2025): ₹12,00,001 to ₹16,00,000 @ 15%"),
            (1600000.0, 2000000.0, 0.20, "Section 115BAC (Finance Act 2025): ₹16,00,001 to ₹20,00,000 @ 20%"),
            (2000000.0, 2400000.0, 0.25, "Section 115BAC (Finance Act 2025): ₹20,00,001 to ₹24,00,000 @ 25%"),
            (2400000.0, None, 0.30, "Section 115BAC (Finance Act 2025): Above ₹24,00,000 @ 30%"),
        ]
        total_tax = 0.0
        slabs = []
        for low, high, rate, clause in thresholds:
            if taxable_income > low:
                taxable_in_slab = (min(taxable_income, high) - low) if high is not None else (taxable_income - low)
                tax_in_slab = taxable_in_slab * rate
                total_tax += tax_in_slab
                slabs.append(
                    SlabDetail(
                        rate=rate,
                        min_income=low,
                        max_income=high,
                        taxable_amount_in_slab=taxable_in_slab,
                        tax=tax_in_slab,
                        clause=clause,
                    )
                )
        return total_tax, slabs

    def compute_surcharge_and_relief(
        self, taxable_income: float, base_tax: float, is_new_regime: bool
    ) -> Tuple[float, float, float, float, List[str]]:
        """
        Computes surcharge rate, raw surcharge, surcharge marginal relief, and net surcharge.
        Thresholds: ₹50L (10%), ₹1Cr (15%), ₹2Cr (25%), ₹5Cr (37% Old only, capped at 25% for New).
        Marginal relief: Total tax + surcharge on income (T + delta) cannot exceed (Tax on T + surcharge on T) + delta.
        """
        audit = []
        if taxable_income <= 5000000.0:
            return 0.0, 0.0, 0.0, 0.0, audit

        # Determine rate
        if taxable_income <= 10000000.0:
            surcharge_rate = 0.10
            threshold = 5000000.0
            prev_surcharge_rate = 0.0
        elif taxable_income <= 20000000.0:
            surcharge_rate = 0.15
            threshold = 10000000.0
            prev_surcharge_rate = 0.10
        elif taxable_income <= 50000000.0:
            surcharge_rate = 0.25
            threshold = 20000000.0
            prev_surcharge_rate = 0.15
        else:
            if is_new_regime:
                surcharge_rate = 0.25  # Capped at 25% under New Regime
                threshold = 20000000.0
                prev_surcharge_rate = 0.15
            else:
                surcharge_rate = 0.37
                threshold = 50000000.0
                prev_surcharge_rate = 0.25

        raw_surcharge = base_tax * surcharge_rate
        total_tax_with_surcharge = base_tax + raw_surcharge

        # Compute tax at threshold T
        if is_new_regime:
            if self.fy == "2024-25":
                tax_at_threshold, _ = self._compute_base_tax_new_regime_24_25(threshold)
            else:
                tax_at_threshold, _ = self._compute_base_tax_new_regime_25_26(threshold)
        else:
            tax_at_threshold, _ = self._compute_base_tax_old_regime(threshold, age=30)

        surcharge_at_threshold = tax_at_threshold * prev_surcharge_rate
        max_allowed_total = tax_at_threshold + surcharge_at_threshold + (taxable_income - threshold)

        marginal_relief = 0.0
        if total_tax_with_surcharge > max_allowed_total:
            marginal_relief = total_tax_with_surcharge - max_allowed_total
            net_surcharge = max(0.0, raw_surcharge - marginal_relief)
            audit.append(
                f"Surcharge Marginal Relief: Total tax ({total_tax_with_surcharge:,.0f}) exceeds threshold cap "
                f"({max_allowed_total:,.0f}). Marginal relief = ₹{marginal_relief:,.0f}"
            )
        else:
            net_surcharge = raw_surcharge

        audit.append(
            f"Surcharge ({int(surcharge_rate*100)}%): Raw = ₹{raw_surcharge:,.0f}, "
            f"Relief = ₹{marginal_relief:,.0f}, Net Surcharge = ₹{net_surcharge:,.0f}"
        )
        return surcharge_rate, raw_surcharge, marginal_relief, net_surcharge, audit

    def calculate_old_regime(self, profile: TaxPayerProfile) -> TaxBreakdown:
        """Complete statutory calculation for Old Regime."""
        audit = [f"--- OLD REGIME CALCULATION ({self.fy}) ---"]
        deductions = self.compute_deductions_old_regime(profile)
        audit.extend(deductions.audit_trail)

        raw_taxable = max(0.0, profile.gross_salary - deductions.total_deductions)
        # Section 288A rounding
        net_taxable_income = round_to_10(raw_taxable)
        audit.append(f"Section 288A: Net Taxable Income = ₹{net_taxable_income:,.0f}")

        # Base tax
        base_tax, slab_details = self._compute_base_tax_old_regime(net_taxable_income, profile.age)
        for s in slab_details:
            audit.append(f"{s.clause}: Tax on ₹{s.taxable_amount_in_slab:,.0f} = ₹{s.tax:,.0f}")
        audit.append(f"Total Base Tax = ₹{base_tax:,.0f}")

        # Section 87A rebate
        rebate_87a = 0.0
        if net_taxable_income <= 500000.0:
            rebate_87a = min(base_tax, 12500.0)
            audit.append(f"Section 87A Rebate: Income <= ₹5,00,000 -> Rebate = ₹{rebate_87a:,.0f}")
        else:
            audit.append("Section 87A: Income > ₹5,00,000 -> No rebate under Old Regime.")

        tax_after_rebate = max(0.0, base_tax - rebate_87a)

        # Surcharge
        sur_rate, sur_raw, sur_relief, net_surcharge, sur_audit = self.compute_surcharge_and_relief(
            net_taxable_income, tax_after_rebate, is_new_regime=False
        )
        audit.extend(sur_audit)

        tax_after_surcharge = tax_after_rebate + net_surcharge

        # Health and Education Cess @ 4%
        cess = tax_after_surcharge * 0.04
        audit.append(f"Finance Act: Health & Education Cess @ 4% on ₹{tax_after_surcharge:,.0f} = ₹{cess:,.2f}")

        # Section 288B Rounding
        total_payable = round_to_10(tax_after_surcharge + cess)
        audit.append(f"Section 288B: Final Total Tax Payable = ₹{total_payable:,.0f}")

        return TaxBreakdown(
            regime="OLD",
            financial_year=self.fy,
            gross_income=profile.gross_salary,
            deductions=deductions,
            net_taxable_income=net_taxable_income,
            base_tax=base_tax,
            slab_details=slab_details,
            rebate_87a=rebate_87a,
            rebate_87a_marginal_relief=0.0,
            tax_after_rebate=tax_after_rebate,
            surcharge_rate=sur_rate,
            surcharge_raw=sur_raw,
            surcharge_marginal_relief=sur_relief,
            net_surcharge=net_surcharge,
            cess_4_pct=cess,
            total_tax_payable=total_payable,
            clause_audit_trail=audit,
        )

    def calculate_new_regime(self, profile: TaxPayerProfile) -> TaxBreakdown:
        """Complete statutory calculation for New Regime (Section 115BAC)."""
        audit = [f"--- NEW REGIME CALCULATION ({self.fy}) ---"]
        deductions = self.compute_deductions_new_regime(profile)
        audit.extend(deductions.audit_trail)

        raw_taxable = max(0.0, profile.gross_salary - deductions.total_deductions)
        net_taxable_income = round_to_10(raw_taxable)
        audit.append(f"Section 288A: Net Taxable Income = ₹{net_taxable_income:,.0f}")

        # Slab calculation
        if self.fy == "2024-25":
            base_tax, slab_details = self._compute_base_tax_new_regime_24_25(net_taxable_income)
            rebate_threshold = 700000.0
            max_rebate = 25000.0
        else:  # FY 2025-26
            base_tax, slab_details = self._compute_base_tax_new_regime_25_26(net_taxable_income)
            rebate_threshold = 1200000.0
            max_rebate = 60000.0

        for s in slab_details:
            audit.append(f"{s.clause}: Tax on ₹{s.taxable_amount_in_slab:,.0f} = ₹{s.tax:,.0f}")
        audit.append(f"Total Base Tax = ₹{base_tax:,.0f}")

        # Section 87A Rebate & Section 87A Marginal Relief Proviso
        rebate_87a = 0.0
        rebate_87a_marginal_relief = 0.0
        tax_after_rebate = base_tax

        if net_taxable_income <= rebate_threshold:
            rebate_87a = min(base_tax, max_rebate)
            tax_after_rebate = 0.0
            audit.append(
                f"Section 87A Proviso: Income <= ₹{rebate_threshold:,.0f} -> Full Rebate of ₹{rebate_87a:,.0f}. Tax = ₹0"
            )
        else:
            # Proviso to Section 87A for New Regime:
            # Tax payable cannot exceed the amount by which income exceeds the rebate threshold!
            excess_income = net_taxable_income - rebate_threshold
            if base_tax > excess_income:
                rebate_87a_marginal_relief = base_tax - excess_income
                tax_after_rebate = excess_income
                audit.append(
                    f"Section 87A Marginal Relief Proviso: Base tax (₹{base_tax:,.0f}) exceeds excess income "
                    f"(₹{excess_income:,.0f}) over ₹{rebate_threshold:,.0f}. "
                    f"Relief = ₹{rebate_87a_marginal_relief:,.0f}. Tax after 87A = ₹{tax_after_rebate:,.0f}"
                )
            else:
                audit.append(
                    f"Section 87A: Income exceeds ₹{rebate_threshold:,.0f} and base tax (₹{base_tax:,.0f}) <= excess income "
                    f"(₹{excess_income:,.0f}). No 87A relief applies."
                )

        # Surcharge
        sur_rate, sur_raw, sur_relief, net_surcharge, sur_audit = self.compute_surcharge_and_relief(
            net_taxable_income, tax_after_rebate, is_new_regime=True
        )
        audit.extend(sur_audit)

        tax_after_surcharge = tax_after_rebate + net_surcharge

        # Health and Education Cess @ 4%
        cess = tax_after_surcharge * 0.04
        audit.append(f"Finance Act: Health & Education Cess @ 4% on ₹{tax_after_surcharge:,.0f} = ₹{cess:,.2f}")

        # Section 288B Rounding
        total_payable = round_to_10(tax_after_surcharge + cess)
        audit.append(f"Section 288B: Final Total Tax Payable = ₹{total_payable:,.0f}")

        return TaxBreakdown(
            regime="NEW",
            financial_year=self.fy,
            gross_income=profile.gross_salary,
            deductions=deductions,
            net_taxable_income=net_taxable_income,
            base_tax=base_tax,
            slab_details=slab_details,
            rebate_87a=rebate_87a,
            rebate_87a_marginal_relief=rebate_87a_marginal_relief,
            tax_after_rebate=tax_after_rebate,
            surcharge_rate=sur_rate,
            surcharge_raw=sur_raw,
            surcharge_marginal_relief=sur_relief,
            net_surcharge=net_surcharge,
            cess_4_pct=cess,
            total_tax_payable=total_payable,
            clause_audit_trail=audit,
        )

    def compare_regimes(self, profile: TaxPayerProfile) -> RegimeComparison:
        """
        Runs both regimes, compares them, provides optimal recommendation and explanation.
        """
        old_res = self.calculate_old_regime(profile)
        new_res = self.calculate_new_regime(profile)

        diff = abs(old_res.total_tax_payable - new_res.total_tax_payable)
        if old_res.total_tax_payable < new_res.total_tax_payable:
            rec = "OLD"
            explanation = (
                f"The Old Regime saves you ₹{diff:,.0f} annually because your total deductions "
                f"(₹{old_res.deductions.total_deductions:,.0f}: HRA, 80C, 80D, 24b) exceed the Old-to-New break-even threshold."
            )
        elif new_res.total_tax_payable < old_res.total_tax_payable:
            rec = "NEW"
            explanation = (
                f"The New Regime saves you ₹{diff:,.0f} annually due to lower slab rates, higher standard deduction "
                f"(₹{new_res.deductions.standard_deduction:,.0f}), and expanded Section 87A rebate."
            )
        else:
            rec = "EITHER"
            explanation = f"Both regimes result in the exact same tax liability of ₹{old_res.total_tax_payable:,.0f}."

        return RegimeComparison(
            financial_year=self.fy,
            old_regime=old_res,
            new_regime=new_res,
            recommended_regime=rec,
            tax_difference=diff,
            explanation=explanation,
        )
