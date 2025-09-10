
import argparse, json, sys, os
from .engine import RulesEngine

def main():
    parser = argparse.ArgumentParser(description="Evaluate a user-provided rule over the mock data and events.")
    parser.add_argument("--data-dir", default="data", help="Path to data directory")
    parser.add_argument("--rule-json", help="Path to a JSON file containing a single rule object. If omitted, reads from stdin.")
    parser.add_argument("--events-json", default="data/events.json", help="Path to events JSON list")
    args = parser.parse_args()

    engine = RulesEngine(args.data_dir)

    if args.rule_json:
        with open(args.rule_json, "r") as f:
            rule = json.load(f)
    else:
        rule = json.load(sys.stdin)

    with open(args.events_json, "r") as f:
        events = json.load(f)

    logs = engine.evaluate_rule_over_events(rule, events)
    # Print readable output
    print("=== Evaluation Results ===")
    if not logs:
        print("No actions triggered.")
    else:
        for i, line in enumerate(logs, 1):
            print(f"\n[{i}] {line}")

if __name__ == "__main__":
    main()
