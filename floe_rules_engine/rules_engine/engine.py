
import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import re
from .utils import load_json, idx_by, parse_iso, hours_until, deep_get, render_template

@dataclass
class Context:
    practices: Dict[str, Dict[str, Any]]
    patients: Dict[str, Dict[str, Any]]
    appointments: Dict[str, Dict[str, Any]]
    intakes_by_appt: Dict[str, Dict[str, Any]]

class RulesEngine:
    """
    Loads data sets and accepts user-provided rule objects at runtime.
    It does NOT ship with hard-coded rules.
    """
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.practices = idx_by(load_json(f"{data_dir}/practice.json"), "id")
        pts = load_json(f"{data_dir}/patients.json")
        self.patients = idx_by(pts, "id")
        appts = load_json(f"{data_dir}/appointments.json")
        self.appointments = idx_by(appts, "id")
        intakes = load_json(f"{data_dir}/intakes.json")
        self.intakes_by_appt = {x["appointment_id"]: x for x in intakes}

    def build_context(self) -> Context:
        return Context(self.practices, self.patients, self.appointments, self.intakes_by_appt)

    # ---------------- Condition evaluation ----------------

    def match_conditions(self, rule: Dict[str, Any], event: Dict[str, Any], ctx: Context) -> bool:
        conds = rule.get("conditions", {})
        logic = conds.get("logic", "ALL").upper()  # ALL or ANY
        checks: List[bool] = []

        # convenience entities
        appt = None
        if "appointment_id" in event.get("payload", {}):
            appt = ctx.appointments.get(event["payload"]["appointment_id"])
        patient = None
        if appt:
            patient = ctx.patients.get(appt["patient_id"])
        elif "patient_id" in event.get("payload", {}):
            patient = ctx.patients.get(event["payload"]["patient_id"])
        practice = None
        if appt:
            practice = ctx.practices.get(appt["practice_id"])
        elif "practice_id" in event.get("payload", {}):
            practice = ctx.practices.get(event["payload"]["practice_id"])

        # helper to test a single key condition
        def test(key: str, expected: Any) -> bool:
            if key == "event.type":
                return event.get("type") == expected
            if key == "intake_status":
                if not appt: return False
                intake = ctx.intakes_by_appt.get(appt["id"])
                return intake and intake.get("status") == expected
            if key == "appointment_hours_until":
                # use the event.occurred_at as "now" for evaluation
                if not appt: return False
                now = parse_iso(event.get("occurred_at"))
                appt_start = parse_iso(appt["start_time"])
                hrs = hours_until(now, appt_start)
                try:
                    target = float(expected)
                except Exception:
                    return False
                return hrs is not None and 0 <= hrs <= target
            if key == "appointment.status":
                return appt and appt.get("status") == expected
            if key == "appointment.no_show_risk":
                return appt and appt.get("no_show_risk") == expected
            if key == "patient.dnc":
                return patient is not None and bool(patient.get("dnc")) == bool(expected)
            if key == "patient.tags.contains":
                return patient and expected in (patient.get("tags") or [])
            if key == "patient.comm_prefs.sms":
                return patient and bool(patient.get("comm_prefs",{}).get("sms")) == bool(expected)
            if key == "patient.comm_prefs.email":
                return patient and bool(patient.get("comm_prefs",{}).get("email")) == bool(expected)
            if key == "patient.comm_prefs.call":
                return patient and bool(patient.get("comm_prefs",{}).get("call")) == bool(expected)
            # generic deep getter (string equality) for flexibility
            actual = deep_get({
                "event": event,
                "appointment": appt,
                "patient": patient,
                "practice": practice
            }, key)
            return actual == expected

        # iterate all keys except 'logic'
        for k, v in conds.items():
            if k == "logic": 
                continue
            checks.append(test(k, v))

        return all(checks) if logic == "ALL" else any(checks)

    # ---------------- Action expansion ----------------

    def render_action_messages(self, rule: Dict[str, Any], event: Dict[str, Any], ctx: Context) -> List[str]:
        appt = None
        if "appointment_id" in event.get("payload", {}):
            appt = ctx.appointments.get(event["payload"]["appointment_id"])
        patient = None
        if appt:
            patient = ctx.patients.get(appt["patient_id"])
        elif "patient_id" in event.get("payload", {}):
            patient = ctx.patients.get(event["payload"]["patient_id"])
        practice = None
        if appt:
            practice = ctx.practices.get(appt["practice_id"])
        elif "practice_id" in event.get("payload", {}):
            practice = ctx.practices.get(event["payload"]["practice_id"])

        # Comm guardrails
        if patient and patient.get("dnc"):
            return [f"SKIPPED (DNC) for patient {patient['id']}"]
        actions = rule.get("actions", [])
        templates = rule.get("templates", {})
        appointment_time = None
        if appt:
            appointment_time = appt.get("start_time")

        # build a data dict for template rendering
        data = {
            "patient_name": f"{patient.get('first_name','')} {patient.get('last_name','')}" if patient else "",
            "appointment_time": appointment_time or "",
            "practice_name": practice.get("name","") if practice else "",
            "practice_domain": practice.get("domain","") if practice else "",
            "reply_to_email": practice.get("reply_to_email","") if practice else "",
            "sender_phone": practice.get("default_sender_phone","") if practice else "",
            "intake_link": "",
        }
        if appt:
            intake = ctx.intakes_by_appt.get(appt["id"])
            if intake:
                data["intake_link"] = intake.get("link","")

        out = []
        for action in actions:
            tpl = templates.get(action)
            if action.upper() == "SMS":
                msg = render_template(tpl or "Hi {{patient_name}}", data)
                to = patient.get("phone","") if patient else ""
                out.append(f"Triggered SMS ▶ To: {to}\nMessage: {msg}")
            elif action.upper() == "EMAIL":
                subj = ""
                body = ""
                if isinstance(tpl, dict):
                    subj = render_template(tpl.get("subject",""), data)
                    body = render_template(tpl.get("body",""), data)
                else:
                    body = render_template(str(tpl or ""), data)
                to = patient.get("email","") if patient else ""
                out.append(f"Triggered Email ▶ To: {to}\nSubject: {subj}\nBody: {body}")
            elif action.upper() == "CALL":
                script = render_template(tpl or "Call {{patient_name}} about their appointment.", data)
                to = patient.get("phone","") if patient else ""
                out.append(f"Triggered Call ▶ To: {to}\nScript: {script}")
            else:
                out.append(f"UNKNOWN ACTION '{action}' (no-op)")
        return out

    # ---------------- Public API ----------------

    def evaluate_rule_over_events(self, rule: Dict[str, Any], events: List[Dict[str, Any]]) -> List[str]:
        ctx = self.build_context()
        logs: List[str] = []
        for ev in events:
            if self.match_conditions(rule, ev, ctx):
                logs.extend(self.render_action_messages(rule, ev, ctx))
        return logs
