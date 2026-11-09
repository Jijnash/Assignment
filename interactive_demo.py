"""
Interactive Defense CLI for Fire AI Take-Home Assignment.
Allows you to demonstrate live calculations, free-text parsing, and data quality checks
interactively during your defense interview.

Usage:
  python interactive_demo.py
"""

import sys
from project_a.parser.free_text_parser import PlainLanguageTaxParser
from project_a.hand_coded.calculator import HandCodedTaxCalculator
from project_a.llm_compiled.compiler import CompiledRulesInterpreter, COMPILED_RULES_FY24_25, COMPILED_RULES_FY25_26
from project_b.detectors.rules_detectors import RuleBasedDetectors
from project_b.hybrid_pipeline import HybridDataQualityPipeline


def demo_tax():
    print("\n--- PROJECT A: INTERACTIVE TAX CALCULATOR & PARSER ---")
    print("Enter any plain-language tax query (English, Hinglish, informal, incomplete, or contradictory).")
    print("Type 'back' to return to main menu.\n")

    parser = PlainLanguageTaxParser()
    calc_24 = HandCodedTaxCalculator("2024-25")
    calc_25 = HandCodedTaxCalculator("2025-26")

    while True:
        try:
            query = input("\n[Tax Query] > ").strip()
            if not query:
                continue
            if query.lower() == "back":
                break

            parsed = parser.parse(query)
            if parsed.is_clarification_needed:
                print("\n[SYSTEM HALTED: CLARIFICATION NEEDED]")
                print(f"Missing Fields : {parsed.missing_fields}")
                print(f"Ambiguities    : {parsed.ambiguities}")
                print(f"Question       : {parsed.clarification_question}")
            else:
                profile = parsed.extracted_profile
                print("\n[EXTRACTED TAXPAYER PROFILE]")
                print(f"Gross Salary   : Rs. {profile.gross_salary:,.0f}")
                print(f"Basic Salary   : Rs. {profile.basic_salary:,.0f}")
                print(f"City / Metro   : {profile.city or 'Not specified'} (Metro: {profile.is_metro})")
                print(f"Rent Paid      : Rs. {profile.rent_paid:,.0f} / year")
                print(f"HRA Received   : Rs. {profile.hra_received:,.0f} / year")
                print(f"Section 80C    : Rs. {profile.section_80c:,.0f}")
                print(f"Section 80D    : Rs. {profile.section_80d_self:,.0f} (Parents: Rs. {profile.section_80d_parents:,.0f})")

                # FY 24-25
                res24 = calc_24.compare_regimes(profile)
                print(f"\n--- FY 2024-25 (Current AY 2025-26) ---")
                print(f"Old Regime Tax : Rs. {res24.old_regime.total_tax_payable:,.0f}")
                print(f"New Regime Tax : Rs. {res24.new_regime.total_tax_payable:,.0f}")
                print(f"Recommendation : {res24.recommended_regime} REGIME (Saves Rs. {res24.tax_difference:,.0f})")

                # FY 25-26
                res25 = calc_25.compare_regimes(profile)
                print(f"\n--- FY 2025-26 (Budget 2025 Amendments) ---")
                print(f"Old Regime Tax : Rs. {res25.old_regime.total_tax_payable:,.0f}")
                print(f"New Regime Tax : Rs. {res25.new_regime.total_tax_payable:,.0f}")
                print(f"Recommendation : {res25.recommended_regime} REGIME (Saves Rs. {res25.tax_difference:,.0f})")
        except (KeyboardInterrupt, EOFError):
            break


def demo_data_quality():
    print("\n--- PROJECT B: INTERACTIVE DATA QUALITY PIPELINE ---")
    print("Testing sample record through the 3-Tier Hybrid Pipeline...")

    sample_record = {
        "Unique Key": 99990001,
        "Created Date": "2023-05-10T14:00:00.000",
        "Closed Date": "2023-05-09T10:00:00.000",  # Inverted!
        "Agency": "NYPD",
        "Complaint Type": "Noise - Residential",
        "Descriptor": "Loud Music/Party",
        "Incident Zip": "10001",
        "Borough": "BROOKLYN",  # Inconsistent!
        "Latitude": -73.9851,   # Swapped!
        "Longitude": 40.7484,   # Swapped!
        "Status": "Closed",
        "Resolution Description": (
            "The Police Department responded. Officer contacted complainant at 212-555-0199. "
            "However, the building manager was not present and the complaint remains UNRESOLVED."
        ),
    }

    pipeline = HybridDataQualityPipeline()
    res = pipeline.process_batch([sample_record])

    print("\n[INJECTED DIRTY ROW]")
    for k, v in sample_record.items():
        print(f"  {k:22s}: {v}")

    print("\n[HYBRID PIPELINE VERDICT]")
    print(f"Total Rows Flagged : {res['flagged_rows_count']} / {res['total_rows_processed']}")
    print(f"LLM Calls Made     : {res['llm_calls_made']} (Routed for semantic contradiction check)")
    print(f"Estimated Cost/1M  : ${res['cost_per_million_rows_usd']}")


def main():
    while True:
        print("\n" + "=" * 60)
        print(" FIRE AI TAKE-HOME ASSIGNMENT: INTERACTIVE DEFENSE CLI ")
        print("=" * 60)
        print("1. Test Indian Income Tax Engine (Free-text parsing & rules)")
        print("2. Test NYC 311 Data Quality Pipeline (Multi-defect detection)")
        print("3. Exit")
        choice = input("\nSelect an option [1-3]: ").strip()
        if choice == "1":
            demo_tax()
        elif choice == "2":
            demo_data_quality()
        elif choice == "3":
            print("\nExiting. Good luck with the defense interview!")
            break


if __name__ == "__main__":
    main()
