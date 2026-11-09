"""
NYC 311 2023 Raw Data Profiler (Project B Task 1).
Discovers and documents real data quality issues in raw 2023 records:
- Negative resolution times (Closed Date < Created Date)
- ZIP code vs Borough geographic contradictions
- Swapped Latitude & Longitude coordinates
- PII leaks (phone numbers, emails) in free-text resolution fields
- Status vs Closed Date contradictions
- Agency-specific null spikes
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List

BOROUGH_ZIP_MAP = {
    "MANHATTAN": ("100", "101", "102"),
    "STATEN ISLAND": ("103",),
    "BRONX": ("104",),
    "QUEENS": ("110", "111", "113", "114", "116"),
    "BROOKLYN": ("112",),
}

PHONE_REGEX = re.compile(r"\b(?:\+?1[-.]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


class NYC311Profiler:
    def __init__(self, data_path: str = "project_b/data/nyc_311_2023_sample.json"):
        with open(data_path, "r", encoding="utf-8") as f:
            self.records = json.load(f)

    def profile(self) -> Dict[str, Any]:
        total = len(self.records)
        anomalies = {
            "closed_before_created": [],
            "zip_borough_mismatch": [],
            "lat_lon_swapped": [],
            "pii_leaks": [],
            "status_closed_null_date": [],
            "status_open_with_closed_date": [],
            "nulls_by_column": {},
            "nulls_by_agency": {},
        }

        # Initialize null counts
        for k in self.records[0].keys():
            anomalies["nulls_by_column"][k] = 0

        for r in self.records:
            uk = r.get("Unique Key")
            agency = r.get("Agency", "UNKNOWN")
            if agency not in anomalies["nulls_by_agency"]:
                anomalies["nulls_by_agency"][agency] = {"total_rows": 0, "null_address": 0}
            anomalies["nulls_by_agency"][agency]["total_rows"] += 1

            # Null tracking
            for k, v in r.items():
                if v is None or v == "":
                    anomalies["nulls_by_column"][k] = anomalies["nulls_by_column"].get(k, 0) + 1
                    if k in ["Incident Address", "Street Name"]:
                        anomalies["nulls_by_agency"][agency]["null_address"] += 1

            # 1. Closed date before created date
            c_str = r.get("Created Date")
            cl_str = r.get("Closed Date")
            if c_str and cl_str:
                try:
                    c_dt = datetime.fromisoformat(c_str)
                    cl_dt = datetime.fromisoformat(cl_str)
                    if cl_dt < c_dt:
                        anomalies["closed_before_created"].append({
                            "unique_key": uk,
                            "agency": agency,
                            "created_date": c_str,
                            "closed_date": cl_str,
                            "delta_hours": round((cl_dt - c_dt).total_seconds() / 3600.0, 2),
                        })
                except Exception:
                    pass

            # 2. ZIP code vs Borough mismatch
            zip_val = str(r.get("Incident Zip") or "").strip()[:3]
            borough = str(r.get("Borough") or "").upper().strip()
            if zip_val and borough in BOROUGH_ZIP_MAP:
                valid_prefixes = BOROUGH_ZIP_MAP[borough]
                if not zip_val.startswith(valid_prefixes):
                    anomalies["zip_borough_mismatch"].append({
                        "unique_key": uk,
                        "incident_zip": r.get("Incident Zip"),
                        "borough": borough,
                        "complaint_type": r.get("Complaint Type"),
                    })

            # 3. Lat / Lon swapped
            lat = r.get("Latitude")
            lon = r.get("Longitude")
            if lat is not None and lon is not None:
                # NYC is Lat ~ +40.7, Lon ~ -73.9. If Lat is negative or Lon is positive, they are swapped!
                if lat < 0 and lon > 0:
                    anomalies["lat_lon_swapped"].append({
                        "unique_key": uk,
                        "latitude": lat,
                        "longitude": lon,
                        "address": r.get("Incident Address"),
                    })

            # 4. PII leaks
            res_desc = r.get("Resolution Description") or ""
            desc = r.get("Descriptor") or ""
            combined_text = f"{desc} {res_desc}"
            phones = PHONE_REGEX.findall(combined_text)
            emails = EMAIL_REGEX.findall(combined_text)
            if phones or emails:
                anomalies["pii_leaks"].append({
                    "unique_key": uk,
                    "phones": phones,
                    "emails": emails,
                    "sample_text": res_desc[:120],
                })

            # 5. Status contradictions
            status = r.get("Status")
            if status == "Closed" and not cl_str:
                anomalies["status_closed_null_date"].append(uk)
            elif status in ["Open", "Pending"] and cl_str:
                anomalies["status_open_with_closed_date"].append(uk)

        # Summarize profile
        summary = {
            "total_records_profiled": total,
            "quality_issues": {
                "closed_before_created": {
                    "count": len(anomalies["closed_before_created"]),
                    "rate_pct": round(len(anomalies["closed_before_created"]) / total * 100.0, 3),
                    "examples": anomalies["closed_before_created"][:3],
                },
                "zip_borough_mismatch": {
                    "count": len(anomalies["zip_borough_mismatch"]),
                    "rate_pct": round(len(anomalies["zip_borough_mismatch"]) / total * 100.0, 3),
                    "examples": anomalies["zip_borough_mismatch"][:3],
                },
                "lat_lon_swapped": {
                    "count": len(anomalies["lat_lon_swapped"]),
                    "rate_pct": round(len(anomalies["lat_lon_swapped"]) / total * 100.0, 3),
                    "examples": anomalies["lat_lon_swapped"][:3],
                },
                "pii_leaks": {
                    "count": len(anomalies["pii_leaks"]),
                    "rate_pct": round(len(anomalies["pii_leaks"]) / total * 100.0, 3),
                    "examples": anomalies["pii_leaks"][:3],
                },
            },
            "agency_null_spike_profile": anomalies["nulls_by_agency"],
        }
        return summary


if __name__ == "__main__":
    profiler = NYC311Profiler()
    profile_results = profiler.profile()
    print(json.dumps(profile_results, indent=2))

