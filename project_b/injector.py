"""
NYC 311 Corruption Injector (Project B Task 2).
Injects each of the 12 target data quality problems into clean batches at controlled rates:
a. Renamed or dropped column
b. Column type change (numbers arriving as strings or string floats)
c. Date format switch partway through a batch (ISO 8601 -> MM/DD/YYYY HH:MM:SS)
d. Latitude and longitude swapped
e. Exact duplicates
f. Near-duplicates (same request, slightly altered timestamp or text)
g. Null spike in one agency's records
h. Closed date earlier than created date
i. ZIP code inconsistent with borough
j. Complaint Type inconsistent with Descriptor
k. Resolution Description contradicting Status
l. Personal data (phone numbers, emails, names) inside free-text fields
"""

import copy
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple


class CorruptionInjector:
    def __init__(self, seed: int = 101):
        self.random = random.Random(seed)

    def inject_a_dropped_or_renamed_column(
        self, batch: List[Dict[str, Any]], drop_col: str = "Borough", rename_from: str = "Agency", rename_to: str = "agency_code"
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Problem A: Schema structural change - dropped or renamed column."""
        corrupted = []
        for row in batch:
            r = copy.deepcopy(row)
            if drop_col in r:
                del r[drop_col]
            if rename_from in r:
                r[rename_to] = r.pop(rename_from)
            corrupted.append(r)
        metadata = {
            "type": "a_dropped_or_renamed_column",
            "dropped": drop_col,
            "renamed": {rename_from: rename_to},
            "corrupted_rows": len(batch),
        }
        return corrupted, metadata

    def inject_b_column_type_change(
        self, batch: List[Dict[str, Any]], target_column: str = "Latitude", rate: float = 0.10
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Problem B: Column type change (e.g. numeric floats converted to string text)."""
        corrupted = []
        corrupted_indices = []
        for idx, row in enumerate(batch):
            r = copy.deepcopy(row)
            if self.random.random() < rate and r.get(target_column) is not None:
                # Convert float to string with dirty formatting e.g. "40.7128 deg"
                r[target_column] = f"{r[target_column]} deg N"
                corrupted_indices.append(idx)
            corrupted.append(r)
        return corrupted, corrupted_indices

    def inject_c_date_format_switch(
        self, batch: List[Dict[str, Any]], rate: float = 0.15
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Problem C: Date format switch partway through batch (ISO -> US MM/DD/YYYY)."""
        corrupted = []
        corrupted_indices = []
        for idx, row in enumerate(batch):
            r = copy.deepcopy(row)
            if self.random.random() < rate and r.get("Created Date"):
                try:
                    dt = datetime.fromisoformat(r["Created Date"])
                    # Switch from 2023-05-12T14:30:00 to 05/12/2023 02:30:00 PM
                    r["Created Date"] = dt.strftime("%m/%d/%Y %I:%M:%S %p")
                    corrupted_indices.append(idx)
                except Exception:
                    pass
            corrupted.append(r)
        return corrupted, corrupted_indices

    def inject_d_lat_lon_swapped(
        self, batch: List[Dict[str, Any]], rate: float = 0.08
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Problem D: Latitude and Longitude coordinates swapped."""
        corrupted = []
        corrupted_indices = []
        for idx, row in enumerate(batch):
            r = copy.deepcopy(row)
            if self.random.random() < rate and r.get("Latitude") and r.get("Longitude"):
                r["Latitude"], r["Longitude"] = r["Longitude"], r["Latitude"]
                corrupted_indices.append(idx)
            corrupted.append(r)
        return corrupted, corrupted_indices

    def inject_e_exact_duplicates(
        self, batch: List[Dict[str, Any]], duplicate_count: int = 15
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Problem E: Exact duplicate rows inserted into batch."""
        corrupted = copy.deepcopy(batch)
        corrupted_indices = []
        if len(batch) > duplicate_count:
            chosen = self.random.sample(range(len(batch)), duplicate_count)
            for idx in chosen:
                dup_row = copy.deepcopy(batch[idx])
                insert_pos = self.random.randint(0, len(corrupted))
                corrupted.insert(insert_pos, dup_row)
                corrupted_indices.append(insert_pos)
        return corrupted, corrupted_indices

    def inject_f_near_duplicates(
        self, batch: List[Dict[str, Any]], rate: float = 0.08
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Problem F: Near-duplicates (same request, slightly altered timestamp or typo in text)."""
        corrupted = copy.deepcopy(batch)
        corrupted_indices = []
        num_dups = int(len(batch) * rate)
        if len(batch) > num_dups:
            chosen = self.random.sample(range(len(batch)), num_dups)
            for idx in chosen:
                dup_row = copy.deepcopy(batch[idx])
                # Jitter timestamp by 45 seconds and change address slightly
                if dup_row.get("Created Date"):
                    try:
                        dt = datetime.fromisoformat(dup_row["Created Date"]) + timedelta(seconds=45)
                        dup_row["Created Date"] = dt.strftime("%Y-%m-%dT%H:%M:%S.000")
                    except Exception:
                        pass
                if dup_row.get("Incident Address"):
                    dup_row["Incident Address"] += " FL 2"
                insert_pos = self.random.randint(0, len(corrupted))
                corrupted.insert(insert_pos, dup_row)
                corrupted_indices.append(insert_pos)
        return corrupted, corrupted_indices

    def inject_g_null_spike(
        self, batch: List[Dict[str, Any]], agency: str = "NYPD", null_rate_spike: float = 0.85
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Problem G: Null spike in one agency's records (e.g. NYPD address fields suddenly blank)."""
        corrupted = []
        corrupted_indices = []
        for idx, row in enumerate(batch):
            r = copy.deepcopy(row)
            if r.get("Agency") == agency and self.random.random() < null_rate_spike:
                r["Incident Address"] = None
                r["Street Name"] = None
                r["Incident Zip"] = None
                corrupted_indices.append(idx)
            corrupted.append(r)
        return corrupted, corrupted_indices

    def inject_h_closed_before_created(
        self, batch: List[Dict[str, Any]], rate: float = 0.10
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Problem H: Closed date earlier than created date (temporal inversion)."""
        corrupted = []
        corrupted_indices = []
        for idx, row in enumerate(batch):
            r = copy.deepcopy(row)
            if self.random.random() < rate and r.get("Created Date") and r.get("Status") == "Closed":
                try:
                    c_dt = datetime.fromisoformat(r["Created Date"])
                    # Closed 12 to 72 hours BEFORE created
                    cl_dt = c_dt - timedelta(hours=self.random.randint(12, 72))
                    r["Closed Date"] = cl_dt.strftime("%Y-%m-%dT%H:%M:%S.000")
                    corrupted_indices.append(idx)
                except Exception:
                    pass
            corrupted.append(r)
        return corrupted, corrupted_indices

    def inject_i_zip_borough_mismatch(
        self, batch: List[Dict[str, Any]], rate: float = 0.10
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Problem I: ZIP code inconsistent with borough (e.g. Manhattan ZIP in Brooklyn)."""
        corrupted = []
        corrupted_indices = []
        borough_swaps = {
            "MANHATTAN": "11201",  # Brooklyn ZIP
            "BROOKLYN": "10001",   # Manhattan ZIP
            "QUEENS": "10451",     # Bronx ZIP
            "BRONX": "10301",      # Staten Island ZIP
            "STATEN ISLAND": "11101", # Queens ZIP
        }
        for idx, row in enumerate(batch):
            r = copy.deepcopy(row)
            b = r.get("Borough")
            if self.random.random() < rate and b in borough_swaps:
                r["Incident Zip"] = borough_swaps[b]
                corrupted_indices.append(idx)
            corrupted.append(r)
        return corrupted, corrupted_indices

    def inject_j_complaint_descriptor_mismatch(
        self, batch: List[Dict[str, Any]], rate: float = 0.10
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Problem J: Complaint Type inconsistent with Descriptor (e.g. Blocked Driveway with Loud Music)."""
        corrupted = []
        corrupted_indices = []
        absurd_descriptors = {
            "Blocked Driveway": "Loud Music/Party",
            "Noise - Residential": "Pothole",
            "Street Condition": "Rat Sighting",
            "Water System": "No Access",
            "Rodent": "Blocked Hydrant",
        }
        for idx, row in enumerate(batch):
            r = copy.deepcopy(row)
            c = r.get("Complaint Type")
            if self.random.random() < rate and c in absurd_descriptors:
                r["Descriptor"] = absurd_descriptors[c]
                corrupted_indices.append(idx)
            corrupted.append(r)
        return corrupted, corrupted_indices

    def inject_k_resolution_contradicts_status(
        self, batch: List[Dict[str, Any]], rate: float = 0.10
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Problem K: Resolution Description directly contradicts Status."""
        corrupted = []
        corrupted_indices = []
        for idx, row in enumerate(batch):
            r = copy.deepcopy(row)
            if self.random.random() < rate:
                if r.get("Status") == "Closed":
                    r["Resolution Description"] = (
                        "The Department of Housing Preservation was unable to access the premises. "
                        "The violation remains UNRESOLVED and an emergency re-inspection is pending."
                    )
                    corrupted_indices.append(idx)
                elif r.get("Status") in ["Open", "Pending"]:
                    r["Resolution Description"] = (
                        "The condition was inspected, repaired, and completely resolved on site. Case is finalized."
                    )
                    corrupted_indices.append(idx)
            corrupted.append(r)
        return corrupted, corrupted_indices

    def inject_l_pii_inside_free_text(
        self, batch: List[Dict[str, Any]], rate: float = 0.10
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Problem L: Personal data (phone, email, SSN/names) inside free text."""
        corrupted = []
        corrupted_indices = []
        names = ["Alice Walker", "David Miller", "Sarah Jenkins", "Robert Chen"]
        for idx, row in enumerate(batch):
            r = copy.deepcopy(row)
            if self.random.random() < rate:
                name = self.random.choice(names)
                phone = f"{self.random.randint(212, 917)}-{self.random.randint(200, 899)}-{self.random.randint(1000, 9999)}"
                email = f"{name.lower().replace(' ', '.')}@gmail.com"
                pii_text = f" Complainant contact: {name}, Cell: {phone}, Email: {email}."
                r["Resolution Description"] = (r.get("Resolution Description") or "") + pii_text
                corrupted_indices.append(idx)
            corrupted.append(r)
        return corrupted, corrupted_indices

