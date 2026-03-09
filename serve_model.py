"""CML Model endpoint — ML-powered error classification and severity scoring.

Deployed as a CML Model, this exposes Sentinel's trained scikit-learn classifier
as a REST API. Uses real ML models when available, falls back to rule-based.

Example request:
{
    "error_message": "TypeError: Cannot read properties of undefined (reading 'id')",
    "error_type": "TypeError",
    "stack_trace": "at getUser (auth.ts:42:15)"
}

Example response:
{
    "category": "auth",
    "severity": "high",
    "pattern": "null_reference",
    "recommended_action": "Add null check before accessing property",
    "confidence": 0.85,
    "model_type": "ml"
}
"""
import os
import sys

try:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
except NameError:
    PROJECT_ROOT = os.getcwd()
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from ml.classifier import ErrorClassifier

# Initialize classifier once at module load (loads trained models if available)
_classifier = ErrorClassifier()


def predict(args):
    """CML Model predict function — classifies errors using trained ML models.

    This is the function deployed as a CML Model endpoint.
    Cloudera AI serves this as a REST API automatically.
    """
    error_message = args.get("error_message", "")
    error_type = args.get("error_type", "")
    stack_trace = args.get("stack_trace", "")
    occurrence_count = args.get("occurrence_count", 1)

    return _classifier.predict(
        error_message=error_message,
        error_type=error_type,
        stack_trace=stack_trace,
        occurrence_count=occurrence_count,
    )
