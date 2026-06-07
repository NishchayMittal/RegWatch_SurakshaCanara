"""
Test Data Collector — Person A (Week 1)
Fetches 10–15 real circulars from RBI/SEBI/MCA and saves them as
JSON fixtures in data/circulars/. These are used for:
  - MAP Extractor few-shot prompt engineering (your Week 2 job)
  - Person B's Router Agent KB (departmental mapping examples)
  - Integration tests for the full pipeline

Run:  python -m agents.collect_test_data
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Hardcoded real circular URLs (verified accessible as of June 2025)
# These are the best ones for MAP extraction — they have clear, explicit action points
TEST_CIRCULARS = [
    # ── RBI ─────────────────────────────────────────────────────────────────
    {
        "id": "rbi_001",
        "regulator": "RBI",
        "type": "banking_regulation",
        "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12683&Mode=0",
        "title": "Master Direction - Know Your Customer (KYC) Direction, 2016 (Updated)",
        "expected_maps": ["Implement V-CIP for new customers", "Update KYC records every 2 years for high-risk", "File STR within 7 days"]
    },
    {
        "id": "rbi_002",
        "regulator": "RBI",
        "type": "payment_systems",
        "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12600&Mode=0",
        "title": "Guidelines on Digital Lending",
        "expected_maps": ["Disclose APR to borrowers", "Credit limit changes require borrower consent", "Maintain loan servicing records"]
    },
    {
        "id": "rbi_003",
        "regulator": "RBI",
        "type": "forex",
        "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12542&Mode=0",
        "title": "Foreign Exchange Management (Overseas Investment) Regulations",
        "expected_maps": ["Report OI within 60 days", "Obtain approval for indirect overseas investment > $1B"]
    },
    {
        "id": "rbi_004",
        "regulator": "RBI",
        "type": "it_framework",
        "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12579&Mode=0",
        "title": "Master Direction on IT Governance Risk and Controls",
        "expected_maps": ["Board must approve IT strategy", "Annual IS audit mandatory", "BCP test every 6 months"]
    },
    {
        "id": "rbi_005",
        "regulator": "RBI",
        "type": "priority_sector",
        "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=12527&Mode=0",
        "title": "Priority Sector Lending - Targets and Classification",
        "expected_maps": ["40% of ANBC to PSL", "18% to agriculture", "Submit PSL return quarterly"]
    },

    # ── SEBI ────────────────────────────────────────────────────────────────
    {
        "id": "sebi_001",
        "regulator": "SEBI",
        "type": "mutual_funds",
        "url": "https://www.sebi.gov.in/legal/circulars/mar-2024/review-of-norms-for-mutual-fund-lite-amcs_81213.html",
        "title": "Review of Norms for Mutual Fund Lite AMCs",
        "expected_maps": ["Apply for MF Lite registration by Q3", "Maintain reduced net worth of Rs 35 crore"]
    },
    {
        "id": "sebi_002",
        "regulator": "SEBI",
        "type": "brokers",
        "url": "https://www.sebi.gov.in/legal/circulars/sep-2023/cybersecurity-and-cyber-resilience-framework-cscrf-for-sebi-regulated-entities-res_76688.html",
        "title": "Cybersecurity and Cyber Resilience Framework (CSCRF)",
        "expected_maps": ["Designate CISO", "Submit cyber audit report annually", "Incident reporting within 6 hours"]
    },
    {
        "id": "sebi_003",
        "regulator": "SEBI",
        "type": "listed_entities",
        "url": "https://www.sebi.gov.in/legal/circulars/jul-2023/business-responsibility-and-sustainability-reporting_73854.html",
        "title": "Business Responsibility and Sustainability Reporting (BRSR)",
        "expected_maps": ["Top 1000 listed entities to file BRSR", "ESG assurance mandatory from FY2024-25"]
    },
    {
        "id": "sebi_004",
        "regulator": "SEBI",
        "type": "alternates",
        "url": "https://www.sebi.gov.in/legal/circulars/aug-2023/operating-guidelines-for-self-sponsored-aifs_75118.html",
        "title": "Operating Guidelines for Self-Sponsored AIFs",
        "expected_maps": ["Register as self-sponsored AIF", "Disclose conflict of interest to investors"]
    },

    # ── MCA ─────────────────────────────────────────────────────────────────
    {
        "id": "mca_001",
        "regulator": "MCA",
        "type": "corporate_governance",
        "url": "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/circulars.html",
        "title": "Companies (Accounts) Second Amendment Rules 2023",
        "expected_maps": ["File CSR-2 form annually", "Maintain CSR expenditure records for 3 years"]
    },
    {
        "id": "mca_002",
        "regulator": "MCA",
        "type": "compliance_filing",
        "url": "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/circulars.html",
        "title": "Extension of time for filing e-forms AOC-4 and MGT-7",
        "expected_maps": ["File AOC-4 by extended deadline", "No additional fees till extended date"]
    },
    {
        "id": "mca_003",
        "regulator": "MCA",
        "type": "insolvency",
        "url": "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/circulars.html",
        "title": "IBBI (Insolvency Resolution Process for Corporate Persons) Amendment Regulations",
        "expected_maps": ["Update CoC meeting procedures", "File CIRP progress report monthly"]
    },
]


def collect_and_save(output_dir: str = "data/circulars"):
    """
    Fetch test circulars and save as JSON fixtures.
    Saves both raw text and metadata for MAP extractor few-shot prompts.
    """
    import requests
    from bs4 import BeautifulSoup

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    saved = 0

    for entry in TEST_CIRCULARS:
        out_path = Path(output_dir) / f"{entry['id']}.json"
        if out_path.exists():
            print(f"  ✓ Already saved: {entry['id']}")
            saved += 1
            continue

        print(f"  Fetching {entry['id']}: {entry['title'][:50]}...")
        try:
            resp = requests.get(entry["url"], timeout=15, headers={
                "User-Agent": "RegWatch/1.0 (compliance-research)"
            })
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)

            fixture = {
                **entry,
                "raw_text": text[:8000],    # cap at 8k chars — enough for MAP extraction
                "fetched_at": datetime.utcnow().isoformat(),
                "char_count": len(text),
            }

            with open(out_path, "w") as f:
                json.dump(fixture, f, indent=2, ensure_ascii=False)

            print(f"  ✅ Saved ({len(text)} chars): {out_path}")
            saved += 1

        except Exception as e:
            print(f"  ❌ Failed {entry['id']}: {e}")
            # Save stub so you know which ones need manual download
            stub = {**entry, "raw_text": f"FETCH_FAILED: {e}", "fetched_at": datetime.utcnow().isoformat()}
            with open(out_path, "w") as f:
                json.dump(stub, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Collected {saved}/{len(TEST_CIRCULARS)} circulars → {output_dir}/")
    print(f"Use these as few-shot examples for MAP Extractor in Week 2")
    return saved


def load_fixtures(data_dir: str = "data/circulars") -> list[dict]:
    """Load all saved fixtures — used by MAP Extractor for few-shot prompts."""
    fixtures = []
    for path in sorted(Path(data_dir).glob("*.json")):
        with open(path) as f:
            fixtures.append(json.load(f))
    return fixtures


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collect_and_save()
