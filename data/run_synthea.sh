#!/usr/bin/env bash
# Run Synthea to generate synthetic patients and export CSV.
# Requires: Java 17+, and the Synthea JAR at data/synthea-with-dependencies.jar
#
# Usage (from repository root):
#   ./data/run_synthea.sh [ -p POPULATION ] [ -s SEED ] [ STATE [ CITY ] ]
# Examples:
#   ./data/run_synthea.sh -p 1000 -s 42
#   ./data/run_synthea.sh -p 5000 Massachusetts Boston

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
JAR="${SCRIPT_DIR}/synthea-with-dependencies.jar"
PROPS="${SCRIPT_DIR}/synthea.properties"

if [[ ! -f "$JAR" ]]; then
  echo "Synthea JAR not found at: $JAR"
  echo "Download it with:"
  echo "  curl -L -o data/synthea-with-dependencies.jar https://github.com/synthetichealth/synthea/releases/download/master-branch-latest/synthea-with-dependencies.jar"
  exit 1
fi

if ! command -v java &>/dev/null; then
  echo "Java not found. Install Java 17 or newer (JDK)."
  exit 1
fi

cd "$PROJECT_ROOT"
java -jar "$JAR" -c "$PROPS" "$@"
echo ""
echo "CSV output: data/synthea_output/csv/"
echo "Next: python3 data/synthea_to_hse_schema.py"
