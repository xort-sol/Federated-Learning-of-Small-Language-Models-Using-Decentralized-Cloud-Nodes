"""
Convert Synthea CSV export to HSE-equivalent schema (PatientRecord) and write
patients.jsonl + optional clinical text.

Run after Synthea has been executed and CSV files exist under:
  data/synthea_output/csv/

Reads: patients.csv, conditions.csv, medications.csv, encounters.csv, organizations.csv
Writes: patients.jsonl (and optionally clinical_text/*.txt)
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from collections import defaultdict

# Allow importing hse_schema when run as script from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hse_schema import Condition, Encounter, Medication, PatientRecord


def _date_only(s: str) -> str:
    """Extract YYYY-MM-DD from ISO datetime or date string."""
    if not s or s.strip() == "":
        return ""
    s = s.strip()
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        return s[:10]
    return s


def _get(row: dict, *keys: str, default: str = "") -> str:
    """Get value from CSV row with case-insensitive key lookup (Synthea uses UPPERCASE headers)."""
    for k in keys:
        if k in row and row[k] is not None and str(row[k]).strip() != "":
            return str(row[k]).strip()
        # Try common case variants
        for key in (k.upper(), k.lower(), k.title()):
            if key in row and row[key] is not None and str(row[key]).strip() != "":
                return str(row[key]).strip()
    return default


def load_csv(path: Path) -> list[dict]:
    """Load a CSV file into a list of dicts (keys = header)."""
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_records(
    csv_dir: Path,
    include_deceased: bool = False,
) -> list[PatientRecord]:
    """
    Build one PatientRecord per patient from Synthea CSV files.
    csv_dir should contain patients.csv, conditions.csv, medications.csv,
    encounters.csv, organizations.csv.
    """
    patients_csv = load_csv(csv_dir / "patients.csv")
    conditions_csv = load_csv(csv_dir / "conditions.csv")
    medications_csv = load_csv(csv_dir / "medications.csv")
    encounters_csv = load_csv(csv_dir / "encounters.csv")
    organizations_csv = load_csv(csv_dir / "organizations.csv")

    if not patients_csv:
        raise FileNotFoundError(
            f"No patients found in {csv_dir}. Run Synthea first (e.g. ./data/run_synthea.sh -p 100)"
        )

    org_id_to_name = {}
    for row in organizations_csv:
        oid = _get(row, "Id", "id")
        name = _get(row, "Name", "name", default="Unknown")
        if oid:
            org_id_to_name[oid] = name

    # Group by patient ID (Synthea uses UPPERCASE: PATIENT, START, CODE, etc.)
    conditions_by_patient: dict[str, list] = defaultdict(list)
    for row in conditions_csv:
        pid = _get(row, "Patient", "patient")
        if not pid:
            continue
        conditions_by_patient[pid].append({
            "code": _get(row, "Code", "code"),
            "description": _get(row, "Description", "description"),
            "onset_date": _date_only(_get(row, "Start", "start")),
        })

    medications_by_patient: dict[str, list] = defaultdict(list)
    for row in medications_csv:
        pid = _get(row, "Patient", "patient")
        if not pid:
            continue
        medications_by_patient[pid].append({
            "code": _get(row, "Code", "code"),
            "name": _get(row, "Description", "description"),
            "prescribed_date": _date_only(_get(row, "Start", "start")),
        })

    encounters_by_patient: dict[str, list] = defaultdict(list)
    for row in encounters_csv:
        pid = _get(row, "Patient", "patient")
        if not pid:
            continue
        org_id = _get(row, "Organization", "organization")
        provider = org_id_to_name.get(org_id, "Unknown")
        enc_date = _date_only(_get(row, "Start", "start"))
        desc = _get(row, "Description", "description")
        enc_class = _get(row, "EncounterClass", "encounterclass")
        enc_type = desc or enc_class or "Encounter"
        encounters_by_patient[pid].append({
            "date": enc_date,
            "type": enc_type,
            "provider": provider,
        })

    records = []
    for row in patients_csv:
        pid = _get(row, "Id", "id")
        if not pid:
            continue
        death_date = _get(row, "DeathDate", "deathdate")
        if death_date and not include_deceased:
            continue
        birth = _date_only(_get(row, "BirthDate", "birthdate"))
        gender = _get(row, "Gender", "gender", default="U")
        if gender == "M":
            gender = "Male"
        elif gender == "F":
            gender = "Female"
        address = _get(row, "Address", "address")
        city = _get(row, "City", "city")
        state = _get(row, "State", "state")
        parts = [p for p in [address, city, state] if p]
        address_str = ", ".join(parts) if parts else "Unknown"

        conditions = [
            Condition(c["code"], c["description"], c["onset_date"])
            for c in conditions_by_patient.get(pid, [])
        ]
        medications = [
            Medication(m["code"], m["name"], m["prescribed_date"])
            for m in medications_by_patient.get(pid, [])
        ]
        encs = encounters_by_patient.get(pid, [])
        encs.sort(key=lambda e: e["date"])
        encounters = [Encounter(e["date"], e["type"], e["provider"]) for e in encs]

        # Use a short stable id for our schema (Synthea UUIDs are long)
        patient_id = f"SYN-{pid[:8]}" if len(pid) >= 8 else f"SYN-{pid}"
        records.append(PatientRecord(
            patient_id=patient_id,
            birth_date=birth,
            gender=gender,
            address=address_str,
            conditions=conditions,
            medications=medications,
            encounters=encounters,
        ))
    return records


def main():
    parser = argparse.ArgumentParser(
        description="Convert Synthea CSV export to HSE-equivalent patients.jsonl and optional clinical text."
    )
    parser.add_argument(
        "--csv-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "synthea_output" / "csv",
        help="Directory containing Synthea CSV files (default: data/synthea_output/csv)",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "out",
        help="Output directory for patients.jsonl and clinical_text/ (default: data/out)",
    )
    parser.add_argument(
        "--clinical-text",
        action="store_true",
        help="Also write one .txt file per patient (clinical text for LLM training)",
    )
    parser.add_argument(
        "--include-deceased",
        action="store_true",
        help="Include patients with a death date (default: exclude)",
    )
    args = parser.parse_args()

    records = build_records(args.csv_dir, include_deceased=args.include_deceased)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    out_jsonl = args.output_dir / "patients.jsonl"
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")

    if args.clinical_text:
        text_dir = args.output_dir / "clinical_text"
        text_dir.mkdir(parents=True, exist_ok=True)
        for rec in records:
            (text_dir / f"{rec.patient_id}.txt").write_text(rec.to_clinical_text(), encoding="utf-8")

    print(f"Converted {len(records)} patients from Synthea CSV to HSE-equivalent schema.")
    print(f"Output: {out_jsonl}")
    if args.clinical_text:
        print(f"Clinical text: {args.output_dir / 'clinical_text'}")


if __name__ == "__main__":
    main()
