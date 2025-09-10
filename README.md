
# Floe Rules Engine (Demo)

This repo implements a **rules engine** that takes patient events and triggers actions (SMS/Email/Call) **without any baked-in rules**. You provide a rule at runtime (typed or via a file), and the engine evaluates it across the generated dataset.

## What this demonstrates

- Rules defined in **simple JSON** format with:
  - `conditions` (e.g., `"appointment_hours_until": 24`, `"intake_status": "INCOMPLETE"`, etc.)
  - `actions`: `["SMS", "EMAIL", "CALL"]`
  - `templates` per action using placeholders like `{{patient_name}}`, `{{appointment_time}}`, etc.
- Engine that:
  - Loads datasets from `data/`
  - Processes incoming **events** in `data/events.json`
  - If a rule matches an event, renders and **prints** the triggered actions (no real sends)
- **No built-in rules**: supply any arbitrary rule at runtime
- Dataset contains **120+ patients** and hundreds of appointments / events (**100+ entries overall**)

## Data files (generated)

Located in `data/`:
- `practice.json`
- `patients.json`
- `appointments.json`
- `intakes.json`
- `events.json`

These adhere to the formats shown in the assignment PDF.

## Rule format (example)

```
{
  "id": "intake_24hr",
  "conditions": {
    "logic": "ALL",
    "event.type": "schedule.tick",
    "appointment_hours_until": 24,
    "intake_status": "INCOMPLETE"
  },
  "actions": ["SMS","EMAIL"],
  "templates": {
    "SMS": "Hi {{patient_name}}, please finish your intake before {{appointment_time}}. Link: {{intake_link}}",
    "EMAIL": { "subject": "Reminder: Intake", "body": "Hello {{patient_name}}, complete intake before {{appointment_time}}.\n{{intake_link}}" }
  }
}
```

**Note:** The engine evaluates conditions against each event in `events.json`, using `event.occurred_at` as "now" for time windows like `appointment_hours_until`.

### Supported condition keys

- `event.type` — exact match to the event type
- `appointment_hours_until` — `0 <= hours <= value`
- `intake_status` — `"COMPLETE"` or `"INCOMPLETE"`
- `appointment.status`, `appointment.no_show_risk` — exact match
- `patient.dnc` — `true/false` (DNC blocks actions)
- `patient.comm_prefs.sms|email|call` — `true/false`
- `patient.tags.contains` — exact tag string in patient's `tags`
- Any generic path like `event.payload.appointment_id` via simple deep lookup

## How to run

From the repo root:

```
python -m rules_engine.cli --data-dir data --events-json data/events.json --rule-json examples/sample_rule.json
```

Or **type a rule** (no file) and hit Enter (Ctrl-D to end):

```
python -m rules_engine.cli --data-dir data --events-json data/events.json
{ ... your rule JSON ... }
```

## Output

The CLI prints triggered actions like:

```
Triggered SMS ▶ To: +14155551234
Message: Hi John Doe, please finish your intake before 2025-09-09T10:00:00-07:00.

Triggered Email ▶ To: john.doe@baycare-ortho.com
Subject: Reminder: Intake
Body: Hello John Doe, ...
```

## Notes

- Communication preferences and DNC are respected (DNC => SKIPPED).
- Times are ISO8601 strings. For `appointment_hours_until`, we compare appointment start against the event timestamp.
- This is a demo; real integrations are replaced by printed logs.
```

