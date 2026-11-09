"""
Pytest validation suite for Project A.
Runs assertions against 220 test cases and 50 plain-language inputs.
"""

import json
import os
import pytest
from project_a.models import TaxPayerProfile
from project_a.hand_coded.calculator import HandCodedTaxCalculator
from project_a.llm_compiled.compiler import CompiledRulesInterpreter, COMPILED_RULES_FY24_25
from project_a.parser.free_text_parser import PlainLanguageTaxParser


@pytest.fixture(scope="module")
def suite_data():
    base = os.path.dirname(__file__)
    with open(os.path.join(base, "test_cases.json"), "r", encoding="utf-8") as f:
        cases = json.load(f)
    with open(os.path.join(base, "user_descriptions.json"), "r", encoding="utf-8") as f:
        descriptions = json.load(f)
    return cases, descriptions


def test_hand_coded_vs_compiled_exactness(suite_data):
    """Verifies hand-coded rules and LLM-compiled rules match to the exact rupee across all 220 test cases."""
    cases, _ = suite_data
    calc_hand = HandCodedTaxCalculator("2024-25")
    calc_compiled = CompiledRulesInterpreter(COMPILED_RULES_FY24_25)

    for case in cases:
        profile = TaxPayerProfile(**case["profile"])
        res_hand = calc_hand.compare_regimes(profile)
        res_comp = calc_compiled.compare_regimes(profile)

        # Rupee-exact checks
        assert res_hand.old_regime.total_tax_payable == res_comp.old_regime.total_tax_payable, (
            f"Case {case['test_id']} Old Regime mismatch: hand={res_hand.old_regime.total_tax_payable}, comp={res_comp.old_regime.total_tax_payable}"
        )
        assert res_hand.new_regime.total_tax_payable == res_comp.new_regime.total_tax_payable, (
            f"Case {case['test_id']} New Regime mismatch: hand={res_hand.new_regime.total_tax_payable}, comp={res_comp.new_regime.total_tax_payable}"
        )
        assert res_hand.recommended_regime == res_comp.recommended_regime, (
            f"Case {case['test_id']} Recommendation mismatch: hand={res_hand.recommended_regime}, comp={res_comp.recommended_regime}"
        )


def test_30_official_benchmarks(suite_data):
    """Verifies that the first 30 golden reference cases match official Income Tax Department rules."""
    cases, _ = suite_data
    golden = [c for c in cases if c["category"] == "OFFICIAL_BENCHMARK_30"]
    assert len(golden) == 30, f"Expected 30 golden benchmarks, found {len(golden)}"

    calc = HandCodedTaxCalculator("2024-25")
    for case in golden:
        profile = TaxPayerProfile(**case["profile"])
        res = calc.compare_regimes(profile)
        exp = case["expected_fy24_25"]
        assert res.old_regime.total_tax_payable == exp["old_regime_tax"]
        assert res.new_regime.total_tax_payable == exp["new_regime_tax"]
        assert res.recommended_regime == exp["recommended_regime"]


def test_plain_language_parser(suite_data):
    """Verifies that the parser properly extracts or asks clarifying questions on the 50 queries."""
    _, descriptions = suite_data
    assert len(descriptions) == 50
    parser = PlainLanguageTaxParser()

    clarify_count = 0
    extracted_count = 0

    for item in descriptions:
        res = parser.parse(item["text"])
        if item["expect_clarify"]:
            assert res.is_clarification_needed, f"Expected clarification for {item['id']}: {item['text']}"
            assert res.clarification_question is not None
            clarify_count += 1
        else:
            assert not res.is_clarification_needed, f"Unexpected clarification for {item['id']}: {res.clarification_question}"
            assert res.extracted_profile is not None
            assert res.extracted_profile.gross_salary > 0
            extracted_count += 1

    assert clarify_count == 10  # 5 incomplete + 5 contradictory
    assert extracted_count == 40  # 15 formal + 10 informal + 15 hinglish
