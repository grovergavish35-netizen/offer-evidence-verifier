Phase 6 Step 6A — Smart Evidence Correlation Engine

Copy core/evidence_correlation.py to your project's core/ folder.
Copy tests/test_evidence_correlation.py to your project's tests/ folder.

Run from project root:
  python -m pytest tests/test_evidence_correlation.py -v
  python -m pytest tests/ -q

No changes to core/pipeline.py, dashboard1.py or PDF generator are required in Step 6A.
Next step: integrate correlations into the dashboard, PDF and JSON exports.
