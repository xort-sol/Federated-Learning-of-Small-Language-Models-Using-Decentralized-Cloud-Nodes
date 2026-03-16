# Synthetic HSE-equivalent data (Phase 1.2)

This directory supports **SynthEA-style HSE-equivalent synthetic patient data** using **real Synthea** (MITRE’s Synthetic Patient Population Simulator) plus a converter to our unified schema for federated LLaMA training and MIA evaluation.

## Using real Synthea (recommended)

Synthea is the standard open-source synthetic patient generator. It produces CSV (and FHIR) that we map to our HSE-equivalent schema.

### 1. Prerequisites

- **Java 17 or newer** (JDK). Check with: `java -version`
- **Python 3.9+** (for the converter)

### 2. Download the Synthea JAR

From the [Synthea releases](https://github.com/synthetichealth/synthea/releases) (or use the latest master build):

```bash
curl -L -o data/synthea-with-dependencies.jar \
  https://github.com/synthetichealth/synthea/releases/download/master-branch-latest/synthea-with-dependencies.jar
```

### 3. Generate patients with Synthea

From the **repository root**:

```bash
# Generate 1,000 patients (default location: Massachusetts)
./data/run_synthea.sh -p 1000 -s 42

# Generate 10,000 patients with seed for reproducibility
./data/run_synthea.sh -p 10000 -s 42

# Optional: restrict to a state/city (US locations in Synthea)
./data/run_synthea.sh -p 5000 -s 42 Massachusetts Boston
```

Synthea writes CSV to **`data/synthea_output/csv/`** (configured in `data/synthea.properties`). Files include `patients.csv`, `conditions.csv`, `medications.csv`, `encounters.csv`, `organizations.csv`, etc.

### 4. Convert to HSE-equivalent schema

Run the converter to produce `patients.jsonl` and optional clinical text for LLM training:

```bash
# From repository root
python3 data/synthea_to_hse_schema.py --clinical-text -o data/out

# Custom paths
python3 data/synthea_to_hse_schema.py \
  --csv-dir data/synthea_output/csv \
  -o data/out \
  --clinical-text
```

**Outputs:**

- **`data/out/patients.jsonl`** — One JSON object per patient (our schema). Use this for Dirichlet partitioning (Phase 1.3) and train/val/holdout splits.
- **`data/out/clinical_text/<patient_id>.txt`** — One clinical-text file per patient (when `--clinical-text` is set). Use for LLaMA fine-tuning and MIA.

### 5. Optional: include deceased patients

By default, the converter **excludes** patients with a death date. To include them:

```bash
python3 data/synthea_to_hse_schema.py --clinical-text --include-deceased -o data/out
```

---

## Files in this directory

| File | Purpose |
|------|--------|
| `hse_schema.py` | Unified schema: `PatientRecord`, `Condition`, `Medication`, `Encounter`; `to_clinical_text()`, `to_dict()`, `from_dict()`. |
| `synthea.properties` | Synthea config: CSV export on, output under `data/synthea_output`. |
| `run_synthea.sh` | Runs Synthea JAR with this config; expects JAR at `data/synthea-with-dependencies.jar`. |
| `synthea_to_hse_schema.py` | Converts Synthea CSV → `patients.jsonl` + optional clinical text. |
| `synthea_output/csv/` | Created by Synthea; contains `patients.csv`, `conditions.csv`, etc. |
| `out/` | Created by the converter; contains `patients.jsonl` and optionally `clinical_text/`. |

---

## Schema summary

- **Structured record:** `patient_id`, `birth_date`, `gender`, `address`, `conditions` (code, description, onset_date), `medications` (code, name, prescribed_date), `encounters` (date, type, provider).
- **Clinical text:** One string per patient via `PatientRecord.to_clinical_text()` — used for LLM fine-tuning and MIA member/non-member evaluation.

Synthea uses **SNOMED-CT** and **RxNorm** in its CSV; we keep those codes in our schema. For strict “HSE-equivalent” Irish geography you can post-process addresses or use Synthea’s demographics for other areas if available; the clinical and coding content remains suitable for federated learning experiments.

---

## HSE-equivalent note

Synthea’s default geography is US (e.g. Massachusetts). Our pipeline keeps Synthea’s clinical codes and structure; “HSE-equivalent” here means the **schema and usage** (synthetic Irish-style patient records for training and MIA) rather than Synthea generating Irish locations natively. You can relabel or filter in post-processing if needed.

---

## Minimal test (without Java)

A small set of sample CSV files is under `data/synthea_output/csv/` so you can run the converter without running Synthea:

```bash
python3 data/synthea_to_hse_schema.py --clinical-text -o data/out
```

This converts the sample CSVs (2 patients) to `data/out/patients.jsonl` and `data/out/clinical_text/`.
