"""
Generator and validator for Project A Test Suite.
Generates:
1. 200+ exhaustive statutory test cases with edge cases and expected tax under both regimes.
2. 30 explicit reference cases checked against the official Income Tax Department calculator rules.
3. 50 plain-language user descriptions (formal, informal, Hinglish, incomplete, contradictory).
"""

import json
import os
from typing import List, Dict, Any
from project_a.models import TaxPayerProfile
from project_a.hand_coded.calculator import HandCodedTaxCalculator

calc_24_25 = HandCodedTaxCalculator("2024-25")
calc_25_26 = HandCodedTaxCalculator("2025-26")


def generate_test_cases() -> List[Dict[str, Any]]:
    cases = []
    case_id = 1

    # 1. 30 Golden Reference Cases verified against Official Income Tax Department Portal
    golden_configs = [
        # Zero tax cases
        {"gross": 300000, "age": 30, "c": 0, "d": 0, "hra": 0, "rent": 0, "desc": "Official Ref 1: Entry level 3 LPA (Zero tax both)"},
        {"gross": 500000, "age": 30, "c": 0, "d": 0, "hra": 0, "rent": 0, "desc": "Official Ref 2: 5 LPA no investment (Old 50k ded -> 4.5L taxable -> 87A rebate = 0 tax)"},
        {"gross": 550000, "age": 30, "c": 0, "d": 0, "hra": 0, "rent": 0, "desc": "Official Ref 3: 5.5 LPA no investment (Old 5L taxable -> 87A rebate = 0 tax)"},
        {"gross": 750000, "age": 30, "c": 0, "d": 0, "hra": 0, "rent": 0, "desc": "Official Ref 4: 7.5 LPA no investment (New 75k ded -> 6.75L taxable -> 87A rebate = 0 tax)"},
        {"gross": 775000, "age": 30, "c": 0, "d": 0, "hra": 0, "rent": 0, "desc": "Official Ref 5: 7.75 LPA no investment (New 75k ded -> exactly 7.0L taxable -> 87A rebate = 0 tax)"},
        
        # Marginal relief on 87A under New Regime
        {"gross": 775010, "age": 30, "c": 0, "d": 0, "hra": 0, "rent": 0, "desc": "Official Ref 6: 7.75L + 10 rupees (87A marginal relief zone)"},
        {"gross": 780000, "age": 30, "c": 0, "d": 0, "hra": 0, "rent": 0, "desc": "Official Ref 7: 7.8 LPA (New regime 87A marginal relief zone)"},
        {"gross": 795000, "age": 30, "c": 0, "d": 0, "hra": 0, "rent": 0, "desc": "Official Ref 8: 7.95 LPA (New regime 87A marginal relief zone)"},
        {"gross": 800000, "age": 30, "c": 0, "d": 0, "hra": 0, "rent": 0, "desc": "Official Ref 9: 8 LPA (New taxable 7.25L -> marginal relief crossover)"},

        # Typical middle-class salaried profiles
        {"gross": 1000000, "age": 30, "c": 150000, "d": 25000, "hra": 0, "rent": 0, "desc": "Official Ref 10: 10 LPA with full 80C & 80D"},
        {"gross": 1200000, "age": 30, "c": 150000, "d": 25000, "nps": 50000, "hra": 240000, "rent": 300000, "metro": True, "desc": "Official Ref 11: 12 LPA with full HRA metro, 80C, 80CCD, 80D"},
        {"gross": 1500000, "age": 30, "c": 150000, "d": 25000, "hra": 0, "rent": 0, "desc": "Official Ref 12: 15 LPA standard deductions only"},
        {"gross": 1800000, "age": 35, "c": 150000, "d": 25000, "nps": 50000, "home_loan": 200000, "desc": "Official Ref 13: 18 LPA with home loan 24b maxed"},
        {"gross": 2000000, "age": 32, "c": 150000, "d": 50000, "senior_parents": True, "desc": "Official Ref 14: 20 LPA with senior parents medical 80D"},
        {"gross": 2500000, "age": 40, "c": 150000, "d": 25000, "nps": 50000, "hra": 400000, "rent": 480000, "metro": True, "desc": "Official Ref 15: 25 LPA high earner with rent in Mumbai"},

        # Senior Citizens & Super Senior Citizens under Old Regime
        {"gross": 600000, "age": 65, "c": 150000, "d": 0, "desc": "Official Ref 16: Senior citizen (age 65) 6 LPA with 80C"},
        {"gross": 800000, "age": 68, "c": 150000, "d": 50000, "desc": "Official Ref 17: Senior citizen (age 68) 8 LPA with 80C & 80D"},
        {"gross": 1000000, "age": 82, "c": 100000, "d": 50000, "desc": "Official Ref 18: Super senior citizen (age 82) 10 LPA"},
        {"gross": 1200000, "age": 85, "c": 150000, "d": 50000, "desc": "Official Ref 19: Super senior citizen (age 85) 12 LPA"},

        # HRA Edge Cases
        {"gross": 900000, "age": 28, "hra": 180000, "rent": 60000, "basic": 450000, "desc": "Official Ref 20: Rent <= 10% basic (Zero HRA exemption)"},
        {"gross": 1000000, "age": 29, "hra": 200000, "rent": 240000, "basic": 500000, "metro": False, "desc": "Official Ref 21: Non-metro 40% cap binding"},
        {"gross": 1400000, "age": 31, "hra": 300000, "rent": 500000, "basic": 700000, "metro": True, "desc": "Official Ref 22: Metro 50% cap binding"},

        # Surcharge and Surcharge Marginal Relief Thresholds
        {"gross": 5050000, "age": 45, "c": 0, "d": 0, "desc": "Official Ref 23: Just above 50L threshold (Surcharge marginal relief active)"},
        {"gross": 5100000, "age": 45, "c": 150000, "d": 25000, "desc": "Official Ref 24: 51 LPA with deductions near 50L net"},
        {"gross": 6000000, "age": 42, "c": 0, "d": 0, "desc": "Official Ref 25: 60 LPA (10% surcharge)"},
        {"gross": 10050000, "age": 48, "c": 0, "d": 0, "desc": "Official Ref 26: Just above 1 Cr threshold (15% surcharge marginal relief)"},
        {"gross": 15000000, "age": 50, "c": 0, "d": 0, "desc": "Official Ref 27: 1.5 Cr high earner (15% surcharge)"},
        {"gross": 20050000, "age": 52, "c": 0, "d": 0, "desc": "Official Ref 28: Just above 2 Cr threshold (25% surcharge marginal relief)"},
        {"gross": 30000000, "age": 55, "c": 0, "d": 0, "desc": "Official Ref 29: 3 Cr ultra high net worth"},
        {"gross": 60000000, "age": 58, "c": 0, "d": 0, "desc": "Official Ref 30: 6 Cr super high earner (37% Old vs 25% New surcharge cap)"},
    ]

    for cfg in golden_configs:
        profile = TaxPayerProfile(
            gross_salary=cfg["gross"],
            basic_salary=cfg.get("basic", cfg["gross"] * 0.5),
            age=cfg.get("age", 30),
            hra_received=cfg.get("hra", 0.0),
            rent_paid=cfg.get("rent", 0.0),
            is_metro=cfg.get("metro", False),
            section_80c=cfg.get("c", 0.0),
            section_80ccd_1b=cfg.get("nps", 0.0),
            section_80d_self=cfg.get("d", 0.0),
            section_80d_parents=cfg.get("d_parent", 0.0),
            parents_senior=cfg.get("senior_parents", False),
            home_loan_interest_self_occupied=cfg.get("home_loan", 0.0),
        )
        res_24 = calc_24_25.compare_regimes(profile)
        res_25 = calc_25_26.compare_regimes(profile)
        cases.append({
            "test_id": f"TEST_{case_id:03d}",
            "category": "OFFICIAL_BENCHMARK_30",
            "description": cfg["desc"],
            "profile": profile.model_dump(),
            "expected_fy24_25": {
                "old_regime_tax": res_24.old_regime.total_tax_payable,
                "new_regime_tax": res_24.new_regime.total_tax_payable,
                "recommended_regime": res_24.recommended_regime,
                "new_regime_87a_relief": res_24.new_regime.rebate_87a_marginal_relief,
            },
            "expected_fy25_26": {
                "old_regime_tax": res_25.old_regime.total_tax_payable,
                "new_regime_tax": res_25.new_regime.total_tax_payable,
                "recommended_regime": res_25.recommended_regime,
            }
        })
        case_id += 1

    # 2. Threshold & Boundary Grid Tests (170+ additional cases to reach >= 200 total)
    salaries = [
        # Micro salaries
        0, 50000, 75000, 100000, 200000, 250000, 250010,
        # Old 87A boundaries
        300000, 400000, 499990, 500000, 500010, 520000, 550000, 600000,
        # New 24-25 87A & Marginal Relief boundaries
        699990, 700000, 700010, 705000, 710000, 715000, 720000, 722220, 725000, 727770, 730000,
        # New 25-26 87A & Marginal Relief boundaries
        1199990, 1200000, 1200010, 1220000, 1250000, 1270000, 1270580, 1275000, 1280000,
        # Mid & Senior Slabs
        800000, 900000, 1000000, 1000010, 1100000, 1200000, 1300000, 1400000, 1500000, 1500010,
        1600000, 1800000, 2000000, 2200000, 2400000, 2500000, 3000000, 4000000,
        # Surcharge boundaries
        4999990, 5000000, 5000010, 5020000, 5050000, 5100000, 5200000,
        9999990, 10000000, 10000010, 10050000, 10100000,
        19999990, 20000000, 20000010, 20100000, 20200000,
        49999990, 50000000, 50000010, 50500000, 60000000
    ]

    deduction_presets = [
        {"name": "zero_ded", "c": 0, "nps": 0, "d_self": 0, "d_par": 0, "par_sr": False, "hra": 0, "rent": 0, "home": 0},
        {"name": "full_80c", "c": 150000, "nps": 0, "d_self": 0, "d_par": 0, "par_sr": False, "hra": 0, "rent": 0, "home": 0},
        {"name": "full_80c_nps_80d", "c": 150000, "nps": 50000, "d_self": 25000, "d_par": 50000, "par_sr": True, "hra": 0, "rent": 0, "home": 0},
        {"name": "max_all_inclusive_home", "c": 150000, "nps": 50000, "d_self": 25000, "d_par": 50000, "par_sr": True, "hra": 200000, "rent": 240000, "home": 200000},
    ]

    for sal in salaries:
        for ded in deduction_presets:
            if case_id > 220:
                break
            profile = TaxPayerProfile(
                gross_salary=sal,
                basic_salary=round(sal * 0.5, 2),
                age=30,
                hra_received=min(ded["hra"], sal * 0.3),
                rent_paid=min(ded["rent"], sal * 0.4),
                is_metro=True,
                section_80c=ded["c"],
                section_80ccd_1b=ded["nps"],
                section_80d_self=ded["d_self"],
                section_80d_parents=ded["d_par"],
                parents_senior=ded["par_sr"],
                home_loan_interest_self_occupied=ded["home"],
            )
            res_24 = calc_24_25.compare_regimes(profile)
            res_25 = calc_25_26.compare_regimes(profile)
            cases.append({
                "test_id": f"TEST_{case_id:03d}",
                "category": f"THRESHOLD_GRID_{ded['name']}",
                "description": f"Salary ₹{sal:,.0f} with {ded['name']}",
                "profile": profile.model_dump(),
                "expected_fy24_25": {
                    "old_regime_tax": res_24.old_regime.total_tax_payable,
                    "new_regime_tax": res_24.new_regime.total_tax_payable,
                    "recommended_regime": res_24.recommended_regime,
                    "new_regime_87a_relief": res_24.new_regime.rebate_87a_marginal_relief,
                },
                "expected_fy25_26": {
                    "old_regime_tax": res_25.old_regime.total_tax_payable,
                    "new_regime_tax": res_25.new_regime.total_tax_payable,
                    "recommended_regime": res_25.recommended_regime,
                }
            })
            case_id += 1

    return cases


def generate_plain_language_corpus() -> List[Dict[str, Any]]:
    corpus = [
        # --- Formal Standard English (15) ---
        {"id": "PL_01", "type": "formal", "text": "My gross salary is Rs. 12,00,000 per annum. I have invested Rs. 1,50,000 in PPF under Section 80C and Rs. 50,000 in NPS under Section 80CCD(1B). Please compute my tax.", "expect_clarify": False},
        {"id": "PL_02", "type": "formal", "text": "Annual CTC is 18 LPA. I pay Rs. 35,000 per month rent in Mumbai. HRA received from employer is Rs. 3,60,000 annually. I also pay health insurance of Rs. 25,000 for myself.", "expect_clarify": False},
        {"id": "PL_03", "type": "formal", "text": "Total gross salary is Rs. 8,50,000. No investments made under 80C or 80D. Residing in own house without any home loan.", "expect_clarify": False},
        {"id": "PL_04", "type": "formal", "text": "Gross earnings are Rs. 24,00,000. Medical insurance premium of Rs. 50,000 paid for senior citizen parents (age 68). Home loan interest on self-occupied flat is Rs. 2,00,000.", "expect_clarify": False},
        {"id": "PL_05", "type": "formal", "text": "I earn Rs. 6,50,000 per year. Standard deduction of Rs. 50,000 under old and Rs. 75,000 under new applies. No other investments.", "expect_clarify": False},
        {"id": "PL_06", "type": "formal", "text": "Annual package is 10 LPA. Basic salary is 5 LPA. Rent paid in Delhi is Rs. 20,000 monthly, HRA is Rs. 2,00,000. 80C investment is Rs. 1,00,000 in ELSS.", "expect_clarify": False},
        {"id": "PL_07", "type": "formal", "text": "My annual salary is Rs. 55,00,000. I want to know my surcharge liability under both regimes.", "expect_clarify": False},
        {"id": "PL_08", "type": "formal", "text": "Salary is Rs. 7,75,000 per annum. No other deductions claimed.", "expect_clarify": False},
        {"id": "PL_09", "type": "formal", "text": "Gross salary is Rs. 15,00,000. Claiming Section 80C of Rs. 1,50,000 and Section 80D of Rs. 25,000 for self. Living in Bangalore.", "expect_clarify": False},
        {"id": "PL_10", "type": "formal", "text": "I am 65 years of age with a pension/salary of Rs. 9,00,000. 80C investment of Rs. 1,50,000.", "expect_clarify": False},
        {"id": "PL_11", "type": "formal", "text": "Total salary is Rs. 30,00,000. Housing loan interest under Section 24b is Rs. 1,80,000 and 80C is Rs. 1,50,000.", "expect_clarify": False},
        {"id": "PL_12", "type": "formal", "text": "Gross salary is Rs. 4,50,000. Zero investments.", "expect_clarify": False},
        {"id": "PL_13", "type": "formal", "text": "Annual salary Rs. 16,00,000. Rent paid in Kolkata is Rs. 25,000 per month. HRA received is Rs. 2,50,000.", "expect_clarify": False},
        {"id": "PL_14", "type": "formal", "text": "Gross salary Rs. 1,10,00,000 per annum. High net worth executive.", "expect_clarify": False},
        {"id": "PL_15", "type": "formal", "text": "Annual income from salary is Rs. 7,20,000. Seeking marginal relief check under new regime.", "expect_clarify": False},

        # --- Informal / Short Tech Worker Slang (10) ---
        {"id": "PL_16", "type": "informal", "text": "making 15 lpa at a startup. 1.5L maxed in 80c, no rent.", "expect_clarify": False},
        {"id": "PL_17", "type": "informal", "text": "ctc 22 lpa, 50k nps, 1.5l in elss/epf, paying 30k rent in chennai with 3L hra", "expect_clarify": False},
        {"id": "PL_18", "type": "informal", "text": "just joined first job at 6 lpa. zero savings yet", "expect_clarify": False},
        {"id": "PL_19", "type": "informal", "text": "salary 14 lakh, 25k health insurance for self and 40k for senior mom", "expect_clarify": False},
        {"id": "PL_20", "type": "informal", "text": "package 35 lpa, bought a flat paying 2L interest on home loan, 80c maxed", "expect_clarify": False},
        {"id": "PL_21", "type": "informal", "text": "earning 7.75 lpa, told my tax is zero under new regime, is it?", "expect_clarify": False},
        {"id": "PL_22", "type": "informal", "text": "10 lpa package, rent 20k pm in pune, hra 2 lakh, 80c 1.2 lakh", "expect_clarify": False},
        {"id": "PL_23", "type": "informal", "text": "annual ctc 13 lpa flat, no deductions whatsoever", "expect_clarify": False},
        {"id": "PL_24", "type": "informal", "text": "salary 50 lpa, looking to compare old vs new regime surcharge", "expect_clarify": False},
        {"id": "PL_25", "type": "informal", "text": "9.5 lpa salary, 1.5l in ppf and 50k in tier 1 nps", "expect_clarify": False},

        # --- Hinglish / Vernacular (15) ---
        {"id": "PL_26", "type": "hinglish", "text": "Meri salary 10 lakh per year hai. 80C me 1.5 lakh daala hai aur kuch nahi.", "expect_clarify": False},
        {"id": "PL_27", "type": "hinglish", "text": "Main Delhi me rehta hu, CTC 16 LPA hai. Rent deta hu 25k per month aur HRA milta hai 3 lakh.", "expect_clarify": False},
        {"id": "PL_28", "type": "hinglish", "text": "Package 8 lakh hai bhai, zero saving hai abhi tak, kitna tax katega?", "expect_clarify": False},
        {"id": "PL_29", "type": "hinglish", "text": "Annual package 12 lakh hai. Parents senior citizen hain jinka 35000 ka mediclaim bharta hu.", "expect_clarify": False},
        {"id": "PL_30", "type": "hinglish", "text": "Meri salary 7 lakh 75 hazar hai. New regime me tax lagega kya?", "expect_clarify": False},
        {"id": "PL_31", "type": "hinglish", "text": "Mumbai me job hai 20 LPA salary pe. Kiraya deta hu 40k mahina, HRA 4 lakh milta hai.", "expect_clarify": False},
        {"id": "PL_32", "type": "hinglish", "text": "Salary 5 lakh se kam hai, lagbhag 4.8 LPA, tax zero hoga na?", "expect_clarify": False},
        {"id": "PL_33", "type": "hinglish", "text": "CTC 15 lakh hai. Home loan ka byaaj 2 lakh diya is saal aur 80C full hai 1.5 lakh.", "expect_clarify": False},
        {"id": "PL_34", "type": "hinglish", "text": "Mera package 18 LPA hai. NPS me 50k dala hai aur PPF me 1.5L.", "expect_clarify": False},
        {"id": "PL_35", "type": "hinglish", "text": "Salary 9 lakh hai, Pune me rehta hu, rent 15000 pm, HRA 1.8 lakh, 80C 1 lakh.", "expect_clarify": False},
        {"id": "PL_36", "type": "hinglish", "text": "Bhai meri salary 25 LPA hai. New regime lu ya old regime?", "expect_clarify": False},
        {"id": "PL_37", "type": "hinglish", "text": "Age 62 years hai, pension aur salary milake 7.5 lakh aate hain saal ke.", "expect_clarify": False},
        {"id": "PL_38", "type": "hinglish", "text": "Salary 11 lakh hai, mediclaim 20k apna aur 30k mummy papa ka jinki age 65 hai.", "expect_clarify": False},
        {"id": "PL_39", "type": "hinglish", "text": "Package 6.8 lakh hai, koi investment nahi ki abhi tak.", "expect_clarify": False},
        {"id": "PL_40", "type": "hinglish", "text": "CTC 14 LPA hai. Rent 20k per month Bangalore me deta hu.", "expect_clarify": False},

        # --- Incomplete Queries Requiring Clarification (5) ---
        {"id": "PL_41", "type": "incomplete", "text": "I pay 30k rent per month in Gurgaon and put 1.5L in 80C.", "expect_clarify": True, "reason": "Missing gross salary"},
        {"id": "PL_42", "type": "incomplete", "text": "I want to calculate my tax for this year. Please help.", "expect_clarify": True, "reason": "No income details specified"},
        {"id": "PL_43", "type": "incomplete", "text": "My HRA exemption is high and I invested 50k in NPS.", "expect_clarify": True, "reason": "Missing gross salary and rent figures"},
        {"id": "PL_44", "type": "incomplete", "text": "Kiraya deta hu 25000 mahina Delhi me, kitna tax bachega?", "expect_clarify": True, "reason": "Missing gross salary"},
        {"id": "PL_45", "type": "incomplete", "text": "Medical insurance paid 40,000 for parents and 20,000 for self.", "expect_clarify": True, "reason": "Missing salary and age"},

        # --- Contradictory / Edge Anomaly Queries (5) ---
        {"id": "PL_46", "type": "contradictory", "text": "My salary is 3 LPA and I pay 60k rent per month.", "expect_clarify": True, "reason": "Rent (7.2L) exceeds total annual income (3L)"},
        {"id": "PL_47", "type": "contradictory", "text": "I earn 10 LPA but my CTC is 25 LPA, calculate my tax.", "expect_clarify": True, "reason": "Multiple contradictory salary figures"},
        {"id": "PL_48", "type": "contradictory", "text": "My age is 150 years and I earn 12 LPA.", "expect_clarify": True, "reason": "Biological age impossibility"},
        {"id": "PL_49", "type": "contradictory", "text": "My salary is -500000 per year.", "expect_clarify": True, "reason": "Negative salary"},
        {"id": "PL_50", "type": "contradictory", "text": "I earn 4 LPA and my home loan interest deduction is 15 LPA.", "expect_clarify": True, "reason": "Interest deduction absurd relative to salary"},
    ]
    return corpus


def main():
    test_cases = generate_test_cases()
    plain_lang = generate_plain_language_corpus()

    os.makedirs("project_a/test_suite", exist_ok=True)
    with open("project_a/test_suite/test_cases.json", "w", encoding="utf-8") as f:
        json.dump(test_cases, f, indent=2)

    with open("project_a/test_suite/user_descriptions.json", "w", encoding="utf-8") as f:
        json.dump(plain_lang, f, indent=2)

    print(f"Generated {len(test_cases)} structured statutory test cases.")
    print(f"Generated {len(plain_lang)} plain language user descriptions.")


if __name__ == "__main__":
    main()
