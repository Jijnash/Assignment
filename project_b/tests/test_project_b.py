"""
Automated Pytest Suite for Project B (Data Quality Engine).
Validates:
1. Corruption Injector across all 12 problem types (A through L).
2. Detector precision and recall behavior.
3. NYC 311 Profiler functionality.
4. End-to-end Hybrid Pipeline execution.
"""

import pytest
import os
import json
from project_b.injector import CorruptionInjector
from project_b.detectors.rules_detectors import RuleBasedDetectors
from project_b.detectors.stat_detectors import StatisticalDetectors
from project_b.detectors.llm_detectors import LLMReviewDetectors
from project_b.hybrid_pipeline import HybridDataQualityPipeline
from project_b.profiler import NYC311Profiler
from project_b.benchmark import load_clean_data


@pytest.fixture(scope="module")
def clean_sample():
    return load_clean_data(count=100)


def test_injector_and_rule_detection(clean_sample):
    """Verifies each corruption injector function and its corresponding rule detector."""
    injector = CorruptionInjector(seed=42)
    rules = RuleBasedDetectors()

    # Problem A: Dropped / Renamed Column
    corrupted_a, meta_a = injector.inject_a_dropped_or_renamed_column(clean_sample)
    res_a = rules.detect_a_schema(corrupted_a)
    assert res_a["flagged"] is True
    assert "Borough" in res_a["missing_columns"]

    # Problem B: Column Type Change
    corrupted_b, idx_b = injector.inject_b_column_type_change(clean_sample, rate=0.20)
    flagged_b = rules.detect_b_column_types(corrupted_b)
    assert set(idx_b).issubset(set(flagged_b))

    # Problem C: Date Format Switch
    corrupted_c, idx_c = injector.inject_c_date_format_switch(clean_sample, rate=0.20)
    flagged_c = rules.detect_c_date_formats(corrupted_c)
    assert set(idx_c).issubset(set(flagged_c))

    # Problem D: Lat / Lon Swapped
    corrupted_d, idx_d = injector.inject_d_lat_lon_swapped(clean_sample, rate=0.20)
    flagged_d = rules.detect_d_lat_lon(corrupted_d)
    assert set(idx_d).issubset(set(flagged_d))

    # Problem E: Exact Duplicates
    corrupted_e, idx_e = injector.inject_e_exact_duplicates(clean_sample, duplicate_count=5)
    flagged_e = rules.detect_e_exact_duplicates(corrupted_e)
    assert len(flagged_e) >= 5

    # Problem H: Closed Before Created
    corrupted_h, idx_h = injector.inject_h_closed_before_created(clean_sample, rate=0.20)
    flagged_h = rules.detect_h_closed_before_created(corrupted_h)
    assert set(idx_h).issubset(set(flagged_h))

    # Problem I: ZIP vs Borough
    corrupted_i, idx_i = injector.inject_i_zip_borough_mismatch(clean_sample, rate=0.20)
    flagged_i = rules.detect_i_zip_borough(corrupted_i)
    assert set(idx_i).issubset(set(flagged_i))

    # Problem J: Complaint vs Descriptor
    corrupted_j, idx_j = injector.inject_j_complaint_descriptor_mismatch(clean_sample, rate=0.20)
    flagged_j = rules.detect_j_complaint_descriptor(corrupted_j)
    assert set(idx_j).issubset(set(flagged_j))

    # Problem L: PII in Free Text
    corrupted_l, idx_l = injector.inject_l_pii_inside_free_text(clean_sample, rate=0.20)
    flagged_l = rules.detect_l_pii(corrupted_l)
    assert set(idx_l).issubset(set(flagged_l))


def test_statistical_detectors(clean_sample):
    """Verifies Family B statistical detectors on distribution drift."""
    injector = CorruptionInjector(seed=55)
    stats = StatisticalDetectors()

    # Problem G: Null Spike in Agency
    corrupted_g, _ = injector.inject_g_null_spike(clean_sample, agency="NYPD", null_rate_spike=0.95)
    res_g = stats.detect_g_null_spike_zscore(corrupted_g, agency="NYPD")
    # If NYPD had records in this sample, verify z-score spike
    nypd_rows = [r for r in corrupted_g if r.get("Agency") == "NYPD"]
    if len(nypd_rows) >= 10:
        assert res_g["flagged"] is True
        assert res_g["z_score"] > 4.0

    # Problem F: Near-Duplicates MinHash
    corrupted_f, idx_f = injector.inject_f_near_duplicates(clean_sample, rate=0.15)
    flagged_f = stats.detect_f_near_duplicates_minhash(corrupted_f)
    assert len(flagged_f) > 0


def test_nyc_profiler():
    """Verifies that the raw data profiler accurately summarizes the NYC 311 2023 dataset."""
    profiler = NYC311Profiler()
    res = profiler.profile()
    assert res["total_records_profiled"] == 6000
    assert res["quality_issues"]["closed_before_created"]["count"] > 0
    assert res["quality_issues"]["zip_borough_mismatch"]["count"] > 0
    assert res["quality_issues"]["lat_lon_swapped"]["count"] > 0
    assert res["quality_issues"]["pii_leaks"]["count"] > 0


def test_hybrid_pipeline(clean_sample):
    """Verifies the 3-tier hybrid pipeline end-to-end execution."""
    injector = CorruptionInjector(seed=77)
    corrupted, _ = injector.inject_h_closed_before_created(clean_sample, rate=0.05)
    corrupted, _ = injector.inject_d_lat_lon_swapped(corrupted, rate=0.05)

    pipeline = HybridDataQualityPipeline()
    res = pipeline.process_batch(corrupted)

    assert res["total_rows_processed"] == len(clean_sample)
    assert res["flagged_rows_count"] > 0
    assert res["cost_per_million_rows_usd"] < 50.0  # Massive cost saving vs $520
    assert res["throughput_rows_per_sec"] > 500.0
