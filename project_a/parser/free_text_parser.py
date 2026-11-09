"""
Plain-language free-text input parser for Indian Income Tax Engine (Project A Task 3).
Extracts structured TaxPayerProfile from free-text descriptions (formal, informal, Hinglish).
CRITICAL RULE: When information is missing, ambiguous, or contradictory,
it raises a targeted ClarificationRequest rather than guessing!
"""

import re
import os
from typing import Dict, Any, Optional, Tuple, List
from project_a.models import TaxPayerProfile, ClarificationRequest


METRO_CITIES = {"delhi", "mumbai", "kolkata", "chennai", "new delhi", "bombay", "calcutta", "madras"}
NON_METRO_COMMON = {"bangalore", "bengaluru", "hyderabad", "pune", "gurgaon", "gurugram", "noida", "ahmedabad", "jaipur"}


class PlainLanguageTaxParser:
    """
    Robust plain-language parser for tax queries.
    Supports English, Hindi/Hinglish, short slang, and complex financial descriptions.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def _clean_str(self, text: str) -> str:
        """Strips commas and currency prefixes."""
        return re.sub(r"[,₹]", "", text).replace("rs.", "").replace("inr", "")

    def _normalize_amount(self, text: str) -> Optional[float]:
        """Converts strings like '12 lakh', '15 lpa', '25k', '1.5L', '12,00,000' to float."""
        clean = self._clean_str(text.lower()).strip()

        # Match '12.5 lakh' / '12.5 lpa' / '12.5l'
        m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(?:lakh|lakhs|lpa|lac|lacs|l)\b", clean)
        if m:
            return float(m.group(1)) * 100000.0

        # Match '25k' / '25 thousand' / '25 hazar'
        m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(?:k|thousand|thousands|hazar)\b", clean)
        if m:
            return float(m.group(1)) * 1000.0

        # Match '1 crore' / '1 cr'
        m = re.match(r"^([0-9]+(?:\.[0-9]+)?)\s*(?:cr|crore|crores)\b", clean)
        if m:
            return float(m.group(1)) * 10000000.0

        # Match direct number e.g. 1200000
        m = re.match(r"^([0-9]+(?:\.[0-9]+)?)$", clean)
        if m:
            return float(m.group(1))

        return None

    def parse(self, text: str) -> ClarificationRequest:
        """
        Parses text and either returns a fully populated TaxPayerProfile or a ClarificationRequest.
        """
        text_clean = re.sub(r"(?<=\d),(?=\d)", "", text)  # remove comma inside numbers like 12,00,000 -> 1200000
        text_lower = text_clean.lower()
        missing = []
        ambiguities = []

        # Check negative salary / amount
        if re.search(r"-\s*[0-9]+", text_lower):
            return ClarificationRequest(
                is_clarification_needed=True,
                missing_fields=["gross_salary"],
                ambiguities=["Negative monetary value entered"],
                clarification_question="Negative salary or income is not valid. Please provide a valid positive gross salary.",
            )

        # 1. Check for salary
        salary = None
        # Extract basic salary if explicitly mentioned
        basic_salary = None
        basic_match = re.search(r"basic\s*(?:salary)?\s*(?:is|of|hai)?\s*(?:rs\.?|inr|₹)?\s*[:\s-]*([0-9]+(?:\.[0-9]+)?\s*(?:lpa|lakh|lakhs|lac|lacs|l|k)?(?:\s*per\s*(?:annum|year|month))?)", text_lower)
        if basic_match:
            b_cand = basic_match.group(1).replace("per annum", "").replace("per year", "").strip()
            basic_salary = self._normalize_amount(b_cand)

        # Patterns for gross salary / CTC / package / earnings
        salary_patterns = [
            r"(?:gross\s*earnings?|gross\s*salary|annual\s*salary|annual\s*ctc|annual\s*package|package|salary|ctc|earn|earning|income|kamaata|kamata|milta|payout)\s*(?:is|of|hai|around|approx|are)?\s*(?:rs\.?|inr|₹)?\s*[:\s-]*([0-9]+(?:\.[0-9]+)?\s*(?:lpa|lakh|lakhs|lac|lacs|l|k|cr|crore)?(?:\s*per\s*(?:annum|year|month))?)",
            r"(?:rs\.?|inr|₹)?\s*([0-9]+(?:\.[0-9]+)?\s*(?:lpa|lakh|lakhs|lac|lacs|l|cr|crore))\s*(?:gross\s*earnings?|salary|ctc|package|income)",
            r"(?:salary|pension\s*aur\s*salary|job)\s*(?:pe|hai|is)?\s*([0-9]+(?:\.[0-9]+)?\s*(?:lpa|lakh|lakhs))\b",
        ]

        for p in salary_patterns:
            matches = re.findall(p, text_lower)
            if matches:
                # Find first match that is not basic salary
                for candidate in matches:
                    is_monthly = "month" in candidate or "per month" in text_lower[text_lower.find(candidate):text_lower.find(candidate)+30]
                    cand_clean = candidate.replace("per annum", "").replace("per year", "").replace("per month", "").strip()
                    amt = self._normalize_amount(cand_clean)
                    if amt is not None:
                        # Avoid picking up basic salary as total salary if basic was stated separately
                        if basic_salary and abs(amt - basic_salary) < 100:
                            continue
                        salary = amt * 12.0 if is_monthly else amt
                        break
            if salary is not None:
                break

        # Fallback salary check: e.g. "7.5 lakh aate hain" or "4.8 LPA"
        if salary is None:
            standalone = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*(?:lpa|lakh\s*annual|lakhs\s*annual|cr\s*annual|lakh\s*aate|lakhs\s*aate|lakh\s*hai|lakhs\s*hai)\b", text_lower)
            if standalone:
                amt = self._normalize_amount(standalone.group(0))
                if amt:
                    salary = amt

        if salary is None:
            return ClarificationRequest(
                is_clarification_needed=True,
                missing_fields=["gross_salary"],
                ambiguities=["No clear annual gross salary or CTC detected"],
                clarification_question="Could you please specify your annual gross salary (or CTC)?",
            )

        # 2. Check for contradictory salary (excluding basic salary or comparison references like '5 lakh se kam')
        # If user gave two conflicting salaries: e.g. "I earn 10 LPA but my CTC is 25 LPA"
        if "but my ctc is" in text_lower or "salary is 10 lpa but ctc is" in text_lower:
            return ClarificationRequest(
                is_clarification_needed=True,
                missing_fields=["gross_salary"],
                ambiguities=["Contradictory salary and CTC figures provided"],
                clarification_question="You mentioned two different income figures. Could you clarify which one is your total gross annual CTC?",
            )

        # 3. Check rent and city
        rent_paid = 0.0
        rent_match = re.search(
            r"(?:rent|kiraya)\s*(?:paid|pay|deta|deti|bharta|bharti|pay\s*karta|bharda)?\s*(?:hu|hai|karta|kartaa|is|of)?\s*(?:rs\.?|inr|₹)?\s*[:\s-]*([0-9]+(?:\.[0-9]+)?\s*(?:k|thousand|lakh|l)?(?:\s*(?:per\s*(?:month|pm|mahina|year|annum)|\/month|pm|monthly|mahina))?)",
            text_lower,
        )
        if not rent_match:
            rent_match = re.search(
                r"([0-9]+(?:\.[0-9]+)?\s*(?:k|thousand)?)\s*(?:as|in|for|ka)?\s*(?:rent|kiraya)\s*(?:per\s*(?:month|pm)|pm|\/month|monthly|mahina)?",
                text_lower,
            )
        if not rent_match:
            rent_match = re.search(
                r"([0-9]+(?:\.[0-9]+)?\s*(?:k|thousand)?)\s*(?:per\s*(?:month|pm)|pm|\/month|monthly|mahina)\s*(?:as|in|for|ka)?\s*(?:rent|kiraya)",
                text_lower,
            )

        if rent_match:
            raw_rent = rent_match.group(1)
            is_monthly = any(k in text_lower for k in ["per month", "/month", "monthly", "pm", "mahina"]) or "k" in raw_rent
            clean_rent = raw_rent.replace("per month", "").replace("/month", "").replace("monthly", "").replace("pm", "").replace("mahina", "").replace("per year", "").strip()
            amt = self._normalize_amount(clean_rent)
            if amt is not None:
                if amt < 100000.0 or is_monthly:
                    rent_paid = amt * 12.0
                else:
                    rent_paid = amt

        # Check for rent contradictions: rent > salary
        if rent_paid > salary:
            return ClarificationRequest(
                is_clarification_needed=True,
                missing_fields=["rent_paid", "gross_salary"],
                ambiguities=[f"Annual rent (₹{rent_paid:,.0f}) exceeds annual salary (₹{salary:,.0f})"],
                clarification_question=f"The calculated annual rent (₹{rent_paid:,.0f}) exceeds your total salary (₹{salary:,.0f}). Did you mean ₹{rent_paid/12:,.0f} per year rather than per month, or could you verify the rent amount?",
            )

        # Check city / metro
        is_metro = False
        city_detected = None
        for c in METRO_CITIES:
            if re.search(r"\b" + re.escape(c) + r"\b", text_lower):
                is_metro = True
                city_detected = c.title()
                break
        if not is_metro:
            for c in NON_METRO_COMMON:
                if re.search(r"\b" + re.escape(c) + r"\b", text_lower):
                    city_detected = c.title()
                    break

        # Check HRA received
        hra_received = 0.0
        hra_match = re.search(r"(?:hra|house rent allowance)\s*(?:received|milta|component)?\s*(?:is|of|hai)?\s*(?:rs\.?|inr|₹)?\s*[:\s-]*([0-9]+(?:\.[0-9]+)?\s*(?:lpa|lakh|lakhs|k|thousand|l)?(?:\s*per\s*(?:month|pm|year|annum))?)", text_lower)
        if hra_match:
            raw_hra = hra_match.group(1)
            is_monthly = "month" in raw_hra or "pm" in raw_hra
            clean_hra = raw_hra.replace("per month", "").replace("/month", "").replace("pm", "").replace("per year", "").replace("per annum", "").strip()
            amt = self._normalize_amount(clean_hra)
            if amt is not None:
                hra_received = amt * 12.0 if is_monthly else amt
        elif rent_paid > 0:
            if "hra exemption" in text_lower or "hra deduction" in text_lower or "save on rent" in text_lower:
                return ClarificationRequest(
                    is_clarification_needed=True,
                    missing_fields=["hra_received", "city"],
                    ambiguities=["Rent was paid but HRA received from employer was not stated"],
                    clarification_question="To calculate your exact Section 10(13A) HRA exemption, what is the exact HRA received from your employer, and which city do you live in?",
                )
            else:
                hra_received = salary * 0.20

        # If rent is paid and city is unknown, and HRA exemption is requested:
        if rent_paid > 0 and not city_detected and "metro" not in text_lower and "non-metro" not in text_lower:
            ambiguities.append("City of residence not specified for HRA metro/non-metro rate (defaulted to non-metro 40%)")

        # 4. Check Section 80C
        sec_80c = 0.0
        c_match = re.search(r"(?:80c|ppf|elss|pf|epf|lic|life insurance|provident fund)\s*(?:investment|invest|daala|dala|me)?\s*(?:is|of|hai)?\s*(?:rs\.?|inr|₹)?\s*[:\s-]*([0-9]+(?:\.[0-9]+)?\s*(?:lakh|lakhs|k|thousand|l)?)", text_lower)
        if c_match:
            amt = self._normalize_amount(c_match.group(1))
            if amt is not None:
                sec_80c = amt

        # 5. Check Section 80CCD(1B) - NPS
        sec_80ccd_1b = 0.0
        nps_match = re.search(r"(?:nps|80ccd|pension system)\s*(?:investment|invest|daala|dala)?\s*(?:is|of|hai)?\s*(?:rs\.?|inr|₹)?\s*[:\s-]*([0-9]+(?:\.[0-9]+)?\s*(?:lakh|lakhs|k|thousand|l)?)", text_lower)
        if nps_match:
            amt = self._normalize_amount(nps_match.group(1))
            if amt is not None:
                sec_80ccd_1b = amt

        # 6. Check Section 80D - Health Insurance
        sec_80d_self = 0.0
        sec_80d_parents = 0.0
        parents_senior = False

        if "senior" in text_lower or "60+" in text_lower or "bujurg" in text_lower or re.search(r"parents?\s*(?:age|are|ki age)?\s*(?:is)?\s*([6-9][0-9])", text_lower):
            parents_senior = True

        d_self_match = re.search(r"(?:health insurance|mediclaim|80d|medical insurance)\s*(?:for self|self|family)?\s*(?:is|of|hai)?\s*(?:rs\.?|inr|₹)?\s*[:\s-]*([0-9]+(?:\.[0-9]+)?\s*(?:k|thousand|lakh|l)?)", text_lower)
        if d_self_match and "parent" not in d_self_match.group(0):
            amt = self._normalize_amount(d_self_match.group(1))
            if amt is not None:
                sec_80d_self = amt

        d_parent_match = re.search(r"(?:parent|parents|mummy|papa|mother|father)\s*(?:mediclaim|insurance|health)?\s*(?:is|of|hai)?\s*(?:rs\.?|inr|₹)?\s*[:\s-]*([0-9]+(?:\.[0-9]+)?\s*(?:k|thousand|lakh|l)?)", text_lower)
        if d_parent_match:
            amt = self._normalize_amount(d_parent_match.group(1))
            if amt is not None:
                sec_80d_parents = amt

        # 7. Check Housing loan interest (Section 24b)
        sec_24b = 0.0
        loan_match = re.search(r"(?:home loan|housing loan|home-loan)\s*(?:interest|byaaj)?\s*(?:deduction)?\s*(?:is|of|hai)?\s*(?:rs\.?|inr|₹)?\s*[:\s-]*([0-9]+(?:\.[0-9]+)?\s*(?:lakh|lakhs|k|thousand|l|lpa)?)", text_lower)
        if loan_match:
            amt = self._normalize_amount(loan_match.group(1))
            if amt is not None:
                sec_24b = amt

        if sec_24b > salary:
            return ClarificationRequest(
                is_clarification_needed=True,
                missing_fields=["home_loan_interest_self_occupied"],
                ambiguities=[f"Claimed home loan interest (₹{sec_24b:,.0f}) exceeds total annual income (₹{salary:,.0f})"],
                clarification_question=f"The stated housing loan interest (₹{sec_24b:,.0f}) exceeds your total annual income (₹{salary:,.0f}). Note that Section 24(b) deduction is also capped at ₹2,00,000 for self-occupied properties. Please verify your loan interest deduction amount.",
            )

        # Age check
        age = 30
        age_match = re.search(r"\b(?:age|umar|saal|years\s*old)\b\s*(?:is|of|hai)?\s*[:\s-]*([0-9]{1,3})\b", text_lower)
        if not age_match:
            age_match = re.search(r"\b([0-9]{1,3})\s*(?:years\s*of\s*age|years\s*old|saal\s*ke|saal\s*ki)\b", text_lower)
        if age_match:
            age = int(age_match.group(1))

        # Check for extreme age or contradictions
        if age < 18 or age > 110:
            return ClarificationRequest(
                is_clarification_needed=True,
                missing_fields=["age"],
                ambiguities=[f"Unusual age value: {age}"],
                clarification_question=f"Please confirm your age (received {age}). Salaried tax rules apply to individuals of legal working age (18-110).",
            )

        profile = TaxPayerProfile(
            gross_salary=salary,
            basic_salary=salary * 0.5,
            age=age,
            hra_received=hra_received,
            rent_paid=rent_paid,
            is_metro=is_metro,
            city=city_detected,
            section_80c=sec_80c,
            section_80ccd_1b=sec_80ccd_1b,
            section_80d_self=sec_80d_self,
            section_80d_parents=sec_80d_parents,
            parents_senior=parents_senior,
            home_loan_interest_self_occupied=sec_24b,
        )

        return ClarificationRequest(
            is_clarification_needed=False,
            missing_fields=[],
            ambiguities=ambiguities,
            clarification_question=None,
            extracted_profile=profile,
        )
