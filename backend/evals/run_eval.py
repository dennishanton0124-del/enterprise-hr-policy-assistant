import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.answer_question import answer_question
from backend.evals.eval_cases import EVAL_CASES


def run_evals():
    passed = 0
    failed = 0

    print("\nRunning AI HR Policy Assistant evaluations...\n")

    for case in EVAL_CASES:
        print(f"Test: {case['name']}")

        result = answer_question(case["question"])

        actual = result.get("decision_type")
        expected = case["expected_decision_type"]

        if actual == expected:
            print(f"PASSED | expected={expected}, actual={actual}")
            passed += 1
        else:
            print(f"FAILED | expected={expected}, actual={actual}")
            print(f"Question: {case['question']}")
            print(f"Answer: {result.get('answer')}")
            failed += 1

        print("-" * 50)

    print("\nEvaluation Summary")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total: {passed + failed}")


if __name__ == "__main__":
    run_evals()