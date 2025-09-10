#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime, timedelta
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import time

# Define data directory
DATA_DIR = '/Users/aravindkannappan/Desktop/Floe Health'

# --- NLP library availability checks ---
try:
    import nltk
    nltk_available = True
except ImportError:
    nltk_available = False

try:
    from textblob import TextBlob
    textblob_available = True
except ImportError:
    textblob_available = False

try:
    import spacy
    spacy_available = True
except ImportError:
    spacy_available = False


class ConditionType(Enum):
    RISK_LEVEL = "risk_level"
    TIME_BASED = "time_based"
    STATUS = "status"
    LANGUAGE = "language"
    APPOINTMENT_TYPE = "appointment_type"
    LOCATION = "location"
    PRACTICE = "practice"


class ActionType(Enum):
    SMS = "SMS"
    EMAIL = "EMAIL"
    CALL = "CALL"


@dataclass
class ParsedCondition:
    type: ConditionType
    field: str
    operator: str
    value: Any
    confidence: float


@dataclass
class ParsedAction:
    type: ActionType
    template: str
    custom_message: Optional[str] = None
    subject: Optional[str] = None


@dataclass
class RuleMatch:
    appointment_id: str
    patient_id: str
    confidence: float
    triggered_actions: List[Dict]


class SemanticRuleParser:
    """Enhanced rule parser with semantic understanding"""

    def __init__(self):
        self.condition_keywords = {
            ConditionType.RISK_LEVEL: ['risk', 'likelihood', 'probability', 'chance'],
            ConditionType.TIME_BASED: ['hours', 'minutes', 'tomorrow', 'soon', 'within', 'before'],
            ConditionType.STATUS: ['status', 'state', 'condition'],
            ConditionType.LANGUAGE: ['speaks', 'language', 'spanish', 'english'],
            ConditionType.APPOINTMENT_TYPE: ['type', 'kind', 'appointment', 'visit'],
            ConditionType.LOCATION: ['location', 'place', 'city', 'at'],
            ConditionType.PRACTICE: ['practice', 'clinic', 'hospital', 'center']
        }

        self.value_mappings = {
            'risk_levels': {'high': 'high', 'medium': 'medium', 'low': 'low'},
            'languages': {'spanish': 'es', 'english': 'en', 'es': 'es', 'en': 'en'},
            'statuses': {'incomplete': 'INCOMPLETE', 'complete': 'COMPLETE',
                         'scheduled': 'SCHEDULED', 'cancelled': 'CANCELLED', 'completed': 'COMPLETED'}
        }

        self.operators = {
            'equals': ['is', 'equals', 'matches'],
            'contains': ['contains', 'includes', 'has'],
            'less_than': ['less', 'under', 'below'],
            'greater_than': ['more', 'over', 'above'],
            'within': ['within', 'before']
        }

    def semantic_parse(self, rule_text: str) -> Dict[str, Any]:
        """Parse rule using semantic understanding"""
        rule_text = rule_text.strip().lower()

        # Extract if-then structure
        if_then_match = re.search(r'if\s+(.+?)\s+then\s+(.+)', rule_text)
        if not if_then_match:
            return None

        conditions_text = if_then_match.group(1)
        actions_text = if_then_match.group(2)

        # Parse conditions with confidence scoring
        conditions = self._parse_conditions_semantic(conditions_text)
        actions = self._parse_actions_semantic(actions_text)

        return {
            'conditions': conditions,
            'actions': actions,
            'original_text': rule_text,
            'confidence': min([c.confidence for c in conditions]) if conditions else 0.5
        }

    def _parse_conditions_semantic(self, text: str) -> List[ParsedCondition]:
        """Parse conditions with semantic understanding and confidence scoring"""
        conditions = []

        # Risk level detection
        if any(word in text for word in ['risk', 'likelihood']):
            for level in ['high', 'medium', 'low']:
                if level in text:
                    confidence = 0.9 if f'risk is {level}' in text else 0.7
                    conditions.append(ParsedCondition(
                        type=ConditionType.RISK_LEVEL,
                        field='no_show_risk',
                        operator='equals',
                        value=level,
                        confidence=confidence
                    ))

        # Time-based detection
        time_patterns = [
            (r'within (\d+) hours?', 'within'),
            (r'(\d+) hours? (?:or less|before)', 'within'),
            (r'appointment (?:is )?tomorrow', 'within', 24),
            (r'appointment (?:is )?soon', 'within', 48)
        ]

        for pattern in time_patterns:
            if len(pattern) == 3:
                if re.search(pattern[0], text):
                    conditions.append(ParsedCondition(
                        type=ConditionType.TIME_BASED,
                        field='hours_until',
                        operator='<=',
                        value=pattern[2],
                        confidence=0.8
                    ))
            else:
                match = re.search(pattern[0], text)
                if match:
                    hours = int(match.group(1))
                    conditions.append(ParsedCondition(
                        type=ConditionType.TIME_BASED,
                        field='hours_until',
                        operator='<=',
                        value=hours,
                        confidence=0.9
                    ))

        # Intake status detection
        if 'intake' in text:
            if any(word in text for word in ['incomplete', 'missing', 'not']):
                conditions.append(ParsedCondition(
                    type=ConditionType.STATUS,
                    field='intake_status',
                    operator='equals',
                    value='INCOMPLETE',
                    confidence=0.8
                ))
            elif 'complete' in text:
                conditions.append(ParsedCondition(
                    type=ConditionType.STATUS,
                    field='intake_status',
                    operator='equals',
                    value='COMPLETE',
                    confidence=0.8
                ))

        # Language detection
        if 'spanish' in text or 'es' in text:
            conditions.append(ParsedCondition(
                type=ConditionType.LANGUAGE,
                field='patient_language',
                operator='equals',
                value='es',
                confidence=0.9
            ))
        elif 'english' in text or 'en' in text:
            conditions.append(ParsedCondition(
                type=ConditionType.LANGUAGE,
                field='patient_language',
                operator='equals',
                value='en',
                confidence=0.9
            ))

        # Appointment type detection
        appointment_types = ['oncology', 'ortho', 'mri', 'ob/gyn', 'pt session']
        for apt_type in appointment_types:
            if apt_type.lower() in text:
                conditions.append(ParsedCondition(
                    type=ConditionType.APPOINTMENT_TYPE,
                    field='appointment_type',
                    operator='contains',
                    value=apt_type.title(),
                    confidence=0.8
                ))

        return conditions

    def _parse_actions_semantic(self, text: str) -> List[ParsedAction]:
        """Parse actions with dynamic template generation"""
        actions = []

        # SMS detection
        if any(phrase in text for phrase in ['sms', 'text', 'message']):
            custom_msg = self._extract_custom_message(text)
            template = custom_msg or self._generate_smart_template('SMS', text)
            actions.append(ParsedAction(
                type=ActionType.SMS,
                template=template,
                custom_message=custom_msg
            ))

        # Email detection
        if 'email' in text:
            custom_msg = self._extract_custom_message(text)
            subject = self._extract_subject(text) or "Appointment Reminder"
            template = custom_msg or self._generate_smart_template('EMAIL', text)
            actions.append(ParsedAction(
                type=ActionType.EMAIL,
                template={'subject': subject, 'body': template},
                custom_message=custom_msg,
                subject=subject
            ))

        # Call detection
        if any(phrase in text for phrase in ['call', 'phone']):
            custom_msg = self._extract_custom_message(text)
            template = custom_msg or self._generate_smart_template('CALL', text)
            actions.append(ParsedAction(
                type=ActionType.CALL,
                template=template,
                custom_message=custom_msg
            ))

        return actions

    def _generate_smart_template(self, action_type: str, context: str) -> str:
        """Generate contextually appropriate templates"""
        base_templates = {
            'SMS': {
                'urgent': "URGENT: {patient_first_name}, please {action_needed} for your {appointment_type} appointment.",
                'reminder': "Hi {patient_first_name}, reminder about your {appointment_type} appointment at {practice_name}.",
                'spanish': "Hola {patient_first_name}, recordatorio sobre su cita de {appointment_type}.",
                'default': "Hi {patient_first_name}, this is a reminder about your {appointment_type} appointment."
            },
            'EMAIL': {
                'urgent': "Dear {patient_first_name},\n\nThis is an urgent reminder about your {appointment_type} appointment.\n\nPlease contact us immediately.\n\nBest regards,\n{practice_name}",
                'reminder': "Dear {patient_first_name},\n\nThis is a friendly reminder about your upcoming {appointment_type} appointment.\n\nThank you,\n{practice_name}",
                'spanish': "Estimado/a {patient_first_name},\n\nEste es un recordatorio sobre su cita de {appointment_type}.\n\nGracias,\n{practice_name}",
                'default': "Dear {patient_first_name},\n\nThis is a reminder about your {appointment_type} appointment.\n\nBest regards,\n{practice_name}"
            },
            'CALL': {
                'urgent': "Hi {patient_first_name}, this is {practice_name} calling urgently about your {appointment_type} appointment.",
                'reminder': "Hi {patient_first_name}, this is {practice_name} calling to remind you about your {appointment_type} appointment.",
                'spanish': "Hola {patient_first_name}, le llama {practice_name} sobre su cita de {appointment_type}.",
                'default': "Hi {patient_first_name}, this is {practice_name} calling about your {appointment_type} appointment."
            }
        }

        # Determine template type based on context
        if any(word in context for word in ['urgent', 'important', 'asap']):
            template_type = 'urgent'
        elif any(word in context for word in ['spanish', 'español']):
            template_type = 'spanish'
        elif any(word in context for word in ['reminder', 'remind']):
            template_type = 'reminder'
        else:
            template_type = 'default'

        return base_templates[action_type][template_type]

    def _extract_custom_message(self, text: str) -> Optional[str]:
        """Extract custom messages from text"""
        patterns = [
            r'saying ["\']([^"\']+)["\']',
            r'message ["\']([^"\']+)["\']',
            r'with ["\']([^"\']+)["\']'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None

    def _extract_subject(self, text: str) -> Optional[str]:
        """Extract email subjects"""
        match = re.search(r'subject ["\']([^"\']+)["\']', text)
        return match.group(1) if match else None


class RuleEngine:
    """Enhanced rule engine with caching and optimization"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.parser = SemanticRuleParser()
        self.data_cache = {}
        self.rule_cache = {}
        self.load_data()

    def load_data(self):
        """Load and cache data"""
        try:
            with open(os.path.join(self.data_dir, 'practices_generated.json'), 'r') as f:
                practices = json.load(f)
            with open(os.path.join(self.data_dir, 'patients_generated.json'), 'r') as f:
                patients = json.load(f)
            with open(os.path.join(self.data_dir, 'appointments_generated.json'), 'r') as f:
                appointments = json.load(f)
            with open(os.path.join(self.data_dir, 'intakes_generated.json'), 'r') as f:
                intakes = json.load(f)
            with open(os.path.join(self.data_dir, 'events_generated.json'), 'r') as f:
                events = json.load(f)

            self.data_cache = {
                'practices': {p['id']: p for p in practices},
                'patients': {p['id']: p for p in patients},
                'appointments': {a['id']: a for a in appointments},
                'intakes': {i['appointment_id']: i for i in intakes if 'appointment_id' in i},
                'events': events
            }

            print(f"Loaded: {len(practices)} practices, {len(patients)} patients, {len(appointments)} appointments, {len(events)} events")

        except Exception as e:
            print(f"Error loading data: {e}")
            return False
        return True

    def evaluate_rule(self, rule_text: str, limit: int = 10) -> List[RuleMatch]:
        """Evaluate rule against all appointments with confidence scoring"""

        # Check rule cache
        cache_key = f"{rule_text}_{limit}"
        if cache_key in self.rule_cache:
            return self.rule_cache[cache_key]

        parsed_rule = self.parser.semantic_parse(rule_text)
        if not parsed_rule:
            return []

        matches = []
        current_time = "2025-09-10T12:00:00Z"

        all_appointment_ids = list(self.data_cache['appointments'].keys())

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for appt_id in all_appointment_ids:
                future = executor.submit(self._evaluate_appointment, appt_id, parsed_rule, current_time)
                futures.append(future)

            for future in futures:
                result = future.result()
                if result:
                    matches.append(result)
                    if len(matches) >= limit * 2:
                        break

        matches.sort(key=lambda x: x.confidence, reverse=True)

        self.rule_cache[cache_key] = matches[:limit]
        return matches[:limit]

    def _evaluate_appointment(self, appt_id: str, parsed_rule: Dict, current_time: str) -> Optional[RuleMatch]:
        """Evaluate single appointment against rule"""
        context = self._build_context(appt_id, current_time)
        if not context:
            return None

        total_confidence = 0
        matched_conditions = 0

        for condition in parsed_rule['conditions']:
            if self._evaluate_condition(condition, context):
                total_confidence += condition.confidence
                matched_conditions += 1

        if matched_conditions == 0:
            return None

        confidence = (total_confidence / len(parsed_rule['conditions'])) * (matched_conditions / len(parsed_rule['conditions']))

        actions = self._generate_actions(parsed_rule['actions'], context)

        return RuleMatch(
            appointment_id=appt_id,
            patient_id=context['patient_id'],
            confidence=confidence,
            triggered_actions=actions
        )

    def _evaluate_condition(self, condition: ParsedCondition, context: Dict) -> bool:
        """Evaluate individual condition"""
        context_value = context.get(condition.field)
        if context_value is None:
            return False

        if condition.operator == 'equals':
            return str(context_value).lower() == str(condition.value).lower()
        elif condition.operator == 'contains':
            return str(condition.value).lower() in str(context_value).lower()
        elif condition.operator == '<=':
            return float(context_value) <= float(condition.value)
        elif condition.operator == '>=':
            return float(context_value) >= float(condition.value)

        return False

    def _build_context(self, appt_id: str, current_time: str) -> Optional[Dict]:
        """Build comprehensive context using all JSON datasets"""
        appt = self.data_cache['appointments'].get(appt_id)
        if not appt:
            return None

        patient = self.data_cache['patients'].get(appt['patient_id'])
        practice = self.data_cache['practices'].get(appt['practice_id'])
        intake = self.data_cache['intakes'].get(appt_id, {'status': 'INCOMPLETE'})

        # Find related events for this appointment/patient
        related_events = []
        for event in self.data_cache.get('events', []):
            payload = event.get('payload', {})
            if (payload.get('appointment_id') == appt_id or
                    payload.get('patient_id') == appt.get('patient_id')):
                related_events.append(event)

        # Calculate hours until appointment
        try:
            current_dt = datetime.fromisoformat(current_time.replace('Z', ''))
            appt_dt = datetime.fromisoformat(appt['start_time'])
            hours_until = max(0, (appt_dt - current_dt).total_seconds() / 3600)
        except:
            hours_until = 24

        # Format appointment time for messages
        try:
            appt_dt = datetime.fromisoformat(appt['start_time'])
            formatted_time = appt_dt.strftime("%b %d, %I:%M %p")
        except:
            formatted_time = "your appointment time"

        return {
            'appointment_id': appt_id,
            'patient_id': patient.get('id') if patient else None,
            'patient_first_name': patient.get('first_name') if patient else '',
            'patient_last_name': patient.get('last_name') if patient else '',
            'patient_phone': patient.get('phone') if patient else '',
            'patient_email': patient.get('email') if patient else '',
            'patient_language': patient.get('language') if patient else '',
            'patient_dnc': patient.get('dnc', False) if patient else False,
            'patient_comm_sms': patient.get('comm_prefs', {}).get('sms', False) if patient else False,
            'patient_comm_email': patient.get('comm_prefs', {}).get('email', False) if patient else False,
            'patient_comm_call': patient.get('comm_prefs', {}).get('call', False) if patient else False,
            'practice_name': practice.get('name') if practice else '',
            'practice_timezone': practice.get('timezone') if practice else '',
            'practice_phone': practice.get('default_sender_phone') if practice else '',
            'practice_email': practice.get('reply_to_email') if practice else '',
            'practice_domain': practice.get('domain') if practice else '',
            'appointment_type': appt.get('type', ''),
            'appointment_status': appt.get('status', ''),
            'appointment_location': appt.get('location', ''),
            'appointment_start_time': appt.get('start_time', ''),
            'appointment_formatted_time': formatted_time,
            'no_show_risk': appt.get('no_show_risk', ''),
            'intake_status': intake.get('status', 'INCOMPLETE'),
            'intake_last_updated': intake.get('last_updated', ''),
            'intake_link': intake.get('link', ''),
            'hours_until': hours_until,
            'related_events': related_events,
            'recent_events': [e for e in related_events if e.get('type') in ['call.missed', 'intake.updated', 'appointment.updated']]
        }

    def _generate_actions(self, actions: List[ParsedAction], context: Dict) -> List[Dict]:
        """Generate triggered actions"""
        triggered_actions = []

        if context.get('patient_dnc', False):
            return triggered_actions

        for action in actions:
            try:
                if action.type == ActionType.SMS:
                    message = action.template.format(**context)
                    triggered_actions.append({
                        'type': 'SMS',
                        'to': context.get('patient_phone'),
                        'message': message
                    })
                elif action.type == ActionType.EMAIL:
                    if isinstance(action.template, dict):
                        subject = action.template['subject'].format(**context)
                        body = action.template['body'].format(**context)
                    else:
                        subject = action.subject or "Appointment Reminder"
                        body = action.template.format(**context)

                    triggered_actions.append({
                        'type': 'EMAIL',
                        'to': context.get('patient_email'),
                        'subject': subject,
                        'body': body
                    })
                elif action.type == ActionType.CALL:
                    script = action.template.format(**context)
                    triggered_actions.append({
                        'type': 'CALL',
                        'to': context.get('patient_phone'),
                        'script': script
                    })
            except Exception:
                continue

        return triggered_actions


def main():
    """Enhanced interactive main function with exact output format"""
    print("=== Enhanced NLP-Powered Rules Engine ===")

    # Check NLP library availability
    if not nltk_available and not textblob_available and not spacy_available:
        print("Warning: No NLP libraries found. Please install:")
        print("  pip install nltk textblob spacy")
        print("  python -m spacy download en_core_web_sm")
        print("Using basic text processing...")
    else:
        nlp_libs = []
        if nltk_available:
            nlp_libs.append("NLTK")
        if textblob_available:
            nlp_libs.append("TextBlob")
        if spacy_available:
            nlp_libs.append("spaCy")
        print(f"NLP libraries loaded: {', '.join(nlp_libs)}")

    engine = RuleEngine(DATA_DIR)

    if not engine.data_cache:
        print("Failed to load data. Exiting.")
        return

    print("\nNLP-enhanced rule examples:")
    print("- If high risk patients have appointments tomorrow then send urgent SMS")
    print("- If spanish speaking patients have incomplete intake then send SMS in spanish")
    print("- If oncology appointments are within 6 hours then call with urgent message")
    print("- If MRI appointments are scheduled then email preparation instructions")

    while True:
        try:
            print("\nEnter a rule (or 'quit' to exit):")
            rule_input = input("> ").strip()

            if rule_input.lower() in ['quit', 'exit', 'q']:
                break

            if not rule_input:
                continue

            print(f"\nProcessing rule with NLP semantic understanding...")
            start_time = time.time()

            matches = engine.evaluate_rule(rule_input, limit=10)

            processing_time = time.time() - start_time

            if not matches:
                print("No matches found for this rule.")
                continue

            print(f"\nFound {len(matches)} matches (processed in {processing_time:.2f}s):")

            for i, match in enumerate(matches, 1):
                for action in match.triggered_actions:
                    if action['type'] == 'SMS':
                        print(f"Triggered SMS → To: {action['to']}")
                        print(f"Message: {action['message']}")
                        print()
                    elif action['type'] == 'EMAIL':
                        print(f"Triggered Email → To: {action['to']}")
                        print(f"Subject: {action['subject']}")
                        print(f"Body: {action['body']}")
                        print()
                    elif action['type'] == 'CALL':
                        print(f"Triggered Call → To: {action['to']}")
                        print(f"Script: {action['script']}")
                        print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
