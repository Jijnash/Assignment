"""
Data models for Indian Income Tax Engine (Project A).
Strict typing and Pydantic validation for auditability and compliance.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


class TaxPayerProfile(BaseModel):
    gross_salary: float = Field(..., ge=0, description="Gross salary received in the financial year")
    basic_salary: Optional[float] = Field(None, ge=0, description="Basic salary component (for HRA calculation)")
    age: int = Field(30, ge=0, le=120, description="Age of the taxpayer in years")
    
    # HRA fields
    hra_received: float = Field(0.0, ge=0, description="House Rent Allowance received from employer")
    rent_paid: float = Field(0.0, ge=0, description="Total annual rent paid for residential accommodation")
    is_metro: bool = Field(False, description="Residing in metro city (Delhi, Mumbai, Kolkata, Chennai)")
    city: Optional[str] = Field(None, description="City of residence")
    
    # Chapter VI-A & Other Deductions
    section_80c: float = Field(0.0, ge=0, description="Investments under Sec 80C (EPF, PPF, ELSS, Life Insurance, etc.)")
    section_80ccd_1b: float = Field(0.0, ge=0, description="Additional voluntary contribution to NPS under Sec 80CCD(1B)")
    section_80d_self: float = Field(0.0, ge=0, description="Health insurance premium for self, spouse, dependent children")
    section_80d_parents: float = Field(0.0, ge=0, description="Health insurance premium for parents")
    parents_senior: bool = Field(False, description="Whether parents are senior citizens (age 60+)")
    home_loan_interest_self_occupied: float = Field(0.0, ge=0, description="Interest on housing loan for self-occupied property (Sec 24b)")

    @model_validator(mode="after")
    def populate_defaults(self):
        # If basic salary is not explicitly set, typical salaried structure assumes 40-50% of gross
        # But if rent is paid or HRA received and basic is None, we need to know or calculate conservatively
        if self.basic_salary is None:
            self.basic_salary = round(self.gross_salary * 0.5, 2)
        return self


class SlabDetail(BaseModel):
    rate: float
    min_income: float
    max_income: Optional[float]
    taxable_amount_in_slab: float
    tax: float
    clause: str


class DeductionBreakdown(BaseModel):
    standard_deduction: float = 0.0
    hra_exemption: float = 0.0
    sec_80c: float = 0.0
    sec_80ccd_1b: float = 0.0
    sec_80d: float = 0.0
    sec_24b: float = 0.0
    total_deductions: float = 0.0
    audit_trail: List[str] = Field(default_factory=list)


class TaxBreakdown(BaseModel):
    regime: str
    financial_year: str
    gross_income: float
    deductions: DeductionBreakdown
    net_taxable_income: float
    base_tax: float
    slab_details: List[SlabDetail] = Field(default_factory=list)
    rebate_87a: float = 0.0
    rebate_87a_marginal_relief: float = 0.0
    tax_after_rebate: float = 0.0
    surcharge_rate: float = 0.0
    surcharge_raw: float = 0.0
    surcharge_marginal_relief: float = 0.0
    net_surcharge: float = 0.0
    cess_4_pct: float = 0.0
    total_tax_payable: float = 0.0
    clause_audit_trail: List[str] = Field(default_factory=list)


class RegimeComparison(BaseModel):
    financial_year: str
    old_regime: TaxBreakdown
    new_regime: TaxBreakdown
    recommended_regime: str  # "OLD" or "NEW" or "EITHER"
    tax_difference: float
    explanation: str


class ClarificationRequest(BaseModel):
    is_clarification_needed: bool
    missing_fields: List[str] = Field(default_factory=list)
    ambiguities: List[str] = Field(default_factory=list)
    clarification_question: Optional[str] = None
    extracted_profile: Optional[TaxPayerProfile] = None
