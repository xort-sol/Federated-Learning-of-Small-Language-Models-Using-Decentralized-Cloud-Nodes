"""
Unified schema for SynthEA/Synthea-generated HSE-equivalent synthetic patient data.

Used for centralised/federated training (via clinical_text) and MIA member/non-member splits.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Condition:
    """Diagnosis with ICD-10 / SNOMED code (HSE/Ireland)."""
    code: str
    description: str
    onset_date: str


@dataclass
class Medication:
    """Prescription with ATC/RxNorm code."""
    code: str
    name: str
    prescribed_date: str


@dataclass
class Encounter:
    """Clinical encounter."""
    date: str
    type: str
    provider: str


@dataclass
class PatientRecord:
    """Single synthetic patient record — HSE-equivalent structure."""
    patient_id: str
    birth_date: str
    gender: str
    address: str
    conditions: list[Condition] = field(default_factory=list)
    medications: list[Medication] = field(default_factory=list)
    encounters: list[Encounter] = field(default_factory=list)

    def to_clinical_text(self) -> str:
        """Clinical-text string for LLM training and MIA evaluation."""
        lines = [
            f"Patient ID: {self.patient_id}",
            f"Date of birth: {self.birth_date}",
            f"Gender: {self.gender}",
            f"Address: {self.address}",
            "",
            "Conditions (ICD-10):",
        ]
        for c in self.conditions:
            lines.append(f"  - {c.code}: {c.description} (onset {c.onset_date})")
        lines.append("")
        lines.append("Medications (ATC):")
        for m in self.medications:
            lines.append(f"  - {m.code}: {m.name} (prescribed {m.prescribed_date})")
        lines.append("")
        lines.append("Encounters:")
        for e in self.encounters:
            lines.append(f"  - {e.date}: {e.type} at {e.provider}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to JSON-suitable dict."""
        return {
            "patient_id": self.patient_id,
            "birth_date": self.birth_date,
            "gender": self.gender,
            "address": self.address,
            "conditions": [
                {"code": c.code, "description": c.description, "onset_date": c.onset_date}
                for c in self.conditions
            ],
            "medications": [
                {"code": m.code, "name": m.name, "prescribed_date": m.prescribed_date}
                for m in self.medications
            ],
            "encounters": [
                {"date": e.date, "type": e.type, "provider": e.provider}
                for e in self.encounters
            ],
        }

    @classmethod
    def from_dict(cls, d: dict) -> PatientRecord:
        """Load from dict (e.g. from JSON/Parquet)."""
        return cls(
            patient_id=d["patient_id"],
            birth_date=d["birth_date"],
            gender=d["gender"],
            address=d["address"],
            conditions=[
                Condition(c["code"], c["description"], c["onset_date"])
                for c in d.get("conditions", [])
            ],
            medications=[
                Medication(m["code"], m["name"], m["prescribed_date"])
                for m in d.get("medications", [])
            ],
            encounters=[
                Encounter(e["date"], e["type"], e["provider"])
                for e in d.get("encounters", [])
            ],
        )
