#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Starting Aegis Comprehensive Testing Suite..."

ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
RESULTS_DIR="$ROOT_DIR/test_results"
mkdir -p "$RESULTS_DIR"
SUMMARY_MD="$RESULTS_DIR/SUMMARY.md"
SUMMARY_CSV="$RESULTS_DIR/summary.csv"
echo "phase,test,exit_code" > "$SUMMARY_CSV"

run_pytest() {
	local phase="$1"; shift
	local testpath="$1"; shift || true
	echo "[${phase}] pytest ${testpath}"
	if pytest -q "$testpath" >"$RESULTS_DIR/${phase}_$(basename "$testpath").log" 2>&1; then
		echo "${phase},${testpath},0" >> "$SUMMARY_CSV"
	else
		echo "${phase},${testpath},1" >> "$SUMMARY_CSV"
	fi
}

run_sh() {
	local phase="$1"; shift
	local shpath="$1"; shift || true
	echo "[${phase}] sh ${shpath}"
	if bash "$shpath" >"$RESULTS_DIR/${phase}_$(basename "$shpath").log" 2>&1; then
		echo "${phase},${shpath},0" >> "$SUMMARY_CSV"
	else
		echo "${phase},${shpath},1" >> "$SUMMARY_CSV"
	fi
}

# Phase 1: User Experience Testing
echo "Testing User Experience..."
run_pytest UX tests/user_experience/test_configuration_clarity.py
run_pytest UX tests/user_experience/test_ml_engineer_workflow.py
run_sh UX ./tests/user_experience/test_ml_engineer_workflow.sh
run_sh UX ./tests/user_experience/test_healthcare_compliance.sh
run_sh UX ./tests/user_experience/test_non_technical_reports.sh

# Phase 2: Edge Case Testing
echo "Testing Edge Cases..."
run_pytest EDGE tests/edge_cases/test_extreme_datasets.py
run_pytest EDGE tests/edge_cases/test_privacy_parameters.py
run_pytest EDGE tests/edge_cases/test_network_failures.py
run_pytest EDGE tests/edge_cases/test_straggler_retries.py
run_pytest EDGE tests/edge_cases/test_straggler_retries_krum.py

# Phase 3: Security Testing
echo "Running Security Tests..."
run_pytest SECURITY tests/test_attack_membership_inference.py
run_pytest SECURITY tests/test_attack_model_inversion.py
run_pytest SECURITY tests/security/test_attack_metrics_collection.py
run_pytest SECURITY tests/security/test_attack_resilience_api.py
run_sh SECURITY ./tests/security/test_infrastructure_security.sh

# Phase 4: Performance Testing
echo "Performance and Load Testing..."
run_pytest PERF tests/performance/test_training_load.py
run_pytest PERF tests/performance/test_api_load.py
run_sh PERF ./tests/performance/test_stress_scenarios.sh
run_sh PERF ./tests/performance/test_soak_and_scale.sh

# Phase 5: Compliance Testing
echo "Validating Compliance..."
run_pytest COMPLIANCE tests/compliance/test_gdpr_compliance.py
run_pytest COMPLIANCE tests/compliance/test_hipaa_compliance.py
run_pytest COMPLIANCE tests/compliance/test_audit_trails.py
run_pytest COMPLIANCE tests/test_compliance_report_markdown.py
run_pytest COMPLIANCE tests/test_compliance_report_steps_override.py
run_pytest COMPLIANCE tests/test_compliance_pdf.py

# Phase 6: Disaster Recovery Testing
echo "Testing Disaster Recovery..."
run_sh DR ./tests/disaster_recovery/test_crash_recovery.sh
run_sh DR ./tests/disaster_recovery/test_backup_restore.sh

# Summary markdown
{
	echo "# Aegis Comprehensive Test Summary"
	echo
	echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
	echo
	echo "## Results (CSV)"
	echo
	echo '\`\`\`csv'
	cat "$SUMMARY_CSV"
	echo '\`\`\`'
} > "$SUMMARY_MD"

echo "✅ Comprehensive testing complete! See $RESULTS_DIR for logs and summary."
