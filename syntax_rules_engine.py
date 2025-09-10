#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime, timedelta
import sys

# Define data directory
DATA_DIR = '/Users/aravindkannappan/Desktop/Floe Health'

def load_json_files():
    """Load JSON data from the actual files"""
    try:
        with open(os.path.join(DATA_DIR, 'practices_generated.json'), 'r') as f:
            practices = json.load(f)
    except FileNotFoundError:
        print(f"Error: practices_generated.json not found in {DATA_DIR}")
        return None, None, None, None, None
        
    try:
        with open(os.path.join(DATA_DIR, 'patients_generated.json'), 'r') as f:
            patients = json.load(f)
    except FileNotFoundError:
        print(f"Error: patients_generated.json not found in {DATA_DIR}")
        return None, None, None, None, None
        
    try:
        with open(os.path.join(DATA_DIR, 'appointments_generated.json'), 'r') as f:
            appointments = json.load(f)
    except FileNotFoundError:
        print(f"Error: appointments_generated.json not found in {DATA_DIR}")
        return None, None, None, None, None
        
    try:
        with open(os.path.join(DATA_DIR, 'intakes_generated.json'), 'r') as f:
            intakes = json.load(f)
    except FileNotFoundError:
        print(f"Error: intakes_generated.json not found in {DATA_DIR}")
        return None, None, None, None, None
        
    try:
        with open(os.path.join(DATA_DIR, 'events_generated.json'), 'r') as f:
            events = json.load(f)
    except FileNotFoundError:
        print(f"Error: events_generated.json not found in {DATA_DIR}")
        return None, None, None, None, None
    
    return practices, patients, appointments, intakes, events

def create_lookups(practices, patients, appointments, intakes):
    """Create lookup dictionaries"""
    practice_dict = {p['id']: p for p in practices}
    patient_dict = {p['id']: p for p in patients}
    appointment_dict = {a['id']: a for a in appointments}
    intake_dict = {i['appointment_id']: i for i in intakes if 'appointment_id' in i}
    return practice_dict, patient_dict, appointment_dict, intake_dict

def simple_datetime_diff(current_str, appt_str):
    """Calculate hours until appointment"""
    try:
        current_clean = current_str.replace('Z', '').split('+')[0].split('-')[0]
        if 'T' not in current_clean:
            return 24
            
        current_dt = datetime.fromisoformat(current_clean)
        
        if 'T' not in appt_str:
            return 24
        appt_dt = datetime.fromisoformat(appt_str)
        
        diff = appt_dt - current_dt
        return max(0, diff.total_seconds() / 3600)
        
    except Exception as e:
        return 24

class NLPRuleParser:
    """NLP rule parser for user-input rules"""
    
    def __init__(self):
        self.condition_patterns = [
            # No-show risk patterns
            (r'no.?show risk is (high|medium|low)', 'no_show_risk', lambda x: x),
            (r'high risk', 'no_show_risk', lambda x: 'high'),
            (r'medium risk', 'no_show_risk', lambda x: 'medium'),
            (r'low risk', 'no_show_risk', lambda x: 'low'),
            (r'risk is (high|medium|low)', 'no_show_risk', lambda x: x),
            
            # Time-based patterns
            (r'appointment is within (\d+) hours?', 'hours_until', lambda x: {"<=": int(x)}),
            (r'within (\d+) hours?', 'hours_until', lambda x: {"<=": int(x)}),
            (r'(\d+) hours? (?:or less )?(?:until|before|away)', 'hours_until', lambda x: {"<=": int(x)}),
            (r'appointment (?:is )?(?:in )?(\d+) hours?', 'hours_until', lambda x: {"<=": int(x)}),
            (r'appointment (?:is )?tomorrow', 'hours_until', lambda x: {"<=": 24}),
            (r'appointment (?:is )?soon', 'hours_until', lambda x: {"<=": 48}),
            (r'less than (\d+) hours?', 'hours_until', lambda x: {"<=": int(x)}),
            
            # Intake status patterns
            (r'intake is (incomplete|complete)', 'intake_status', lambda x: x.upper()),
            (r'intake (?:form )?(?:not )?(?:filled|submitted|completed)', 'intake_status', lambda x: 'INCOMPLETE'),
            (r'intake (?:form )?(?:is )?incomplete', 'intake_status', lambda x: 'INCOMPLETE'),
            (r'incomplete intake', 'intake_status', lambda x: 'INCOMPLETE'),
            (r'missing intake', 'intake_status', lambda x: 'INCOMPLETE'),
            (r'intake (?:form )?(?:is )?complete', 'intake_status', lambda x: 'COMPLETE'),
            (r'completed intake', 'intake_status', lambda x: 'COMPLETE'),
            
            # Language patterns
            (r'patient speaks (english|spanish|en|es)', 'patient_language', lambda x: x[:2] if len(x) > 2 else x),
            (r'(?:speaks|language is) (english|spanish|en|es)', 'patient_language', lambda x: x[:2] if len(x) > 2 else x),
            (r'spanish.?speaking', 'patient_language', lambda x: 'es'),
            (r'english.?speaking', 'patient_language', lambda x: 'en'),
            
            # Appointment type patterns
            (r'appointment type (?:is |contains )(.+)', 'appointment_type', lambda x: x.strip()),
            (r'(?:type is |type contains )(.+)', 'appointment_type', lambda x: x.strip()),
            (r'oncology', 'appointment_type', lambda x: 'Oncology'),
            (r'ortho', 'appointment_type', lambda x: 'Ortho'),
            (r'mri', 'appointment_type', lambda x: 'MRI'),
            
            # Status patterns
            (r'appointment status is (\w+)', 'appointment_status', lambda x: x.upper()),
            (r'status is (\w+)', 'appointment_status', lambda x: x.upper()),
            (r'scheduled appointment', 'appointment_status', lambda x: 'SCHEDULED'),
            (r'cancelled appointment', 'appointment_status', lambda x: 'CANCELLED'),
            (r'completed appointment', 'appointment_status', lambda x: 'COMPLETED'),
            
            # Location patterns
            (r'location is (.+)', 'appointment_location', lambda x: x.strip()),
            (r'in (.+)', 'appointment_location', lambda x: x.strip()),
            
            # Practice patterns
            (r'practice (?:is |name is )(.+)', 'practice_name', lambda x: x.strip()),
            (r'practice contains (.+)', 'practice_name', lambda x: x.strip()),
        ]
        
        self.action_patterns = [
            (r'send (?:an? )?sms|text (?:them|patient)|sms to patient', 'SMS'),
            (r'send (?:an? )?email|email (?:them|patient)', 'EMAIL'),
            (r'call (?:them|patient)|make (?:a )?call', 'CALL'),
        ]
    
    def parse_rule(self, rule_text):
        """Parse user-input natural language rule"""
        rule_text = rule_text.strip()
        
        # Extract rule ID if provided
        rule_id_match = re.match(r'^(\d+)\.\s*(.+)', rule_text)
        if rule_id_match:
            rule_id = f"rule_{rule_id_match.group(1)}"
            rule_content = rule_id_match.group(2)
        else:
            rule_id = "user_rule"
            rule_content = rule_text
        
        # Parse if-then structure
        if_then_patterns = [
            r'if\s+(.+?)\s+then\s+(.+)',
            r'when\s+(.+?)\s+then\s+(.+)',
            r'if\s+(.+?),\s*(.+)',
        ]
        
        conditions_text = ""
        actions_text = ""
        
        for pattern in if_then_patterns:
            match = re.search(pattern, rule_content, re.IGNORECASE)
            if match:
                conditions_text = match.group(1).strip()
                actions_text = match.group(2).strip()
                break
        
        if not conditions_text or not actions_text:
            print(f"Could not parse rule. Please use format: 'If [condition] then [action]'")
            return None
        
        conditions = self.extract_conditions(conditions_text)
        actions, templates = self.extract_actions(actions_text)
        
        if not actions:
            print(f"No valid actions found. Use 'send SMS', 'send email', or 'call patient'")
            return None
        
        return {
            'id': rule_id,
            'conditions': conditions,
            'actions': actions,
            'templates': templates,
            'original_text': rule_text
        }
    
    def extract_conditions(self, text):
        """Extract conditions from text"""
        conditions = {}
        text_lower = text.lower()
        
        for pattern, field, converter in self.condition_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                try:
                    if match.groups():
                        value = converter(match.group(1))
                    else:
                        value = converter("")
                    conditions[field] = value
                except:
                    continue
        
        return conditions
    
    def extract_actions(self, text):
        """Extract actions from text"""
        actions = []
        templates = {}
        text_lower = text.lower()
        
        for pattern, action in self.action_patterns:
            if re.search(pattern, text_lower):
                actions.append(action)
                
                custom_msg = self.extract_custom_message(text, action.lower())
                
                if action == 'SMS':
                    templates['SMS'] = custom_msg or "Hi {patient_first_name}, this is a reminder about your {appointment_type} appointment."
                elif action == 'EMAIL':
                    subject = self.extract_email_subject(text) or "Appointment Reminder"
                    body = custom_msg or "Dear {patient_first_name},\n\nThis is a reminder about your {appointment_type} appointment.\n\nBest regards,\n{practice_name}"
                    templates['EMAIL'] = {'subject': subject, 'body': body}
                elif action == 'CALL':
                    templates['CALL'] = custom_msg or "Hi {patient_first_name}, this is {practice_name} calling about your {appointment_type} appointment."
        
        return actions, templates
    
    def extract_custom_message(self, text, action_type):
        """Extract custom message"""
        patterns = [
            rf'{action_type}[:\s]+["\']([^"\']+)["\']',
            r'saying ["\']([^"\']+)["\']',
            r'message ["\']([^"\']+)["\']',
            r'with message ["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extract_email_subject(self, text):
        """Extract email subject"""
        subject_match = re.search(r'subject ["\']([^"\']+)["\']', text, re.IGNORECASE)
        return subject_match.group(1) if subject_match else None

def evaluate_rule(rule, context):
    """Evaluate if rule matches context"""
    conditions = rule.get('conditions', {})
    
    if not conditions:
        return True
    
    for condition_key, condition_value in conditions.items():
        context_value = context.get(condition_key)
        
        if context_value is None:
            return False
        
        if isinstance(condition_value, dict):
            for operator, value in condition_value.items():
                if operator == "<=":
                    if not (isinstance(context_value, (int, float)) and context_value <= value):
                        return False
                elif operator == ">=":
                    if not (isinstance(context_value, (int, float)) and context_value >= value):
                        return False
        else:
            if isinstance(context_value, str) and isinstance(condition_value, str):
                if condition_value.lower() not in context_value.lower() and context_value.lower() != condition_value.lower():
                    return False
            elif context_value != condition_value:
                return False
    
    return True

def build_context(appt_id, current_time_str, appointment_dict, patient_dict, practice_dict, intake_dict):
    """Build context for appointment"""
    appt = appointment_dict.get(appt_id)
    if not appt:
        return None
    
    patient = patient_dict.get(appt['patient_id'])
    practice = practice_dict.get(appt['practice_id'])
    intake = intake_dict.get(appt_id, {'status': 'INCOMPLETE'})
    
    hours_until = simple_datetime_diff(current_time_str, appt['start_time'])
    
    return {
        'appointment': appt,
        'patient': patient,
        'practice': practice,
        'intake': intake,
        'hours_until': hours_until,
        'appointment_id': appt.get('id'),
        'appointment_type': appt.get('type'),
        'appointment_status': appt.get('status'),
        'appointment_location': appt.get('location'),
        'no_show_risk': appt.get('no_show_risk'),
        'patient_id': patient.get('id') if patient else None,
        'patient_first_name': patient.get('first_name') if patient else None,
        'patient_language': patient.get('language') if patient else None,
        'patient_dnc': patient.get('dnc') if patient else False,
        'patient_comm_sms': patient.get('comm_prefs', {}).get('sms') if patient else False,
        'patient_comm_email': patient.get('comm_prefs', {}).get('email') if patient else False,
        'patient_comm_call': patient.get('comm_prefs', {}).get('call') if patient else False,
        'practice_name': practice.get('name') if practice else None,
        'intake_status': intake.get('status'),
    }

def trigger_actions(rule, context):
    """Trigger actions for matched rule"""
    patient = context.get('patient')
    practice = context.get('practice')
    
    if not patient or not practice:
        return []
    
    if context.get('patient_dnc', False):
        return []
    
    actions = rule.get('actions', [])
    templates = rule.get('templates', {})
    triggered_actions = []
    
    placeholders = {
        'patient_first_name': context.get('patient_first_name', ''),
        'patient_name': context.get('patient_first_name', ''),
        'practice_name': context.get('practice_name', ''),
        'appointment_type': context.get('appointment_type', ''),
        'appointment_location': context.get('appointment_location', ''),
        'hours_until': str(int(context.get('hours_until', 0))),
    }
    
    for action in actions:
        template = templates.get(action)
        if not template:
            continue
        
        try:
            if action == 'SMS':
                message = template.format(**placeholders)
                triggered_actions.append({
                    'type': 'SMS',
                    'to': patient.get('phone'),
                    'message': message
                })
            elif action == 'EMAIL':
                subject = template['subject'].format(**placeholders)
                body = template['body'].format(**placeholders)
                triggered_actions.append({
                    'type': 'EMAIL',
                    'to': patient.get('email'),
                    'subject': subject,
                    'body': body
                })
            elif action == 'CALL':
                script = template.format(**placeholders)
                triggered_actions.append({
                    'type': 'CALL',
                    'to': patient.get('phone'),
                    'script': script
                })
        except Exception as e:
            continue
    
    return triggered_actions

def print_examples():
    """Print rule examples for users"""
    print("\n=== Rule Examples ===")
    print("Here are some example rules you can try:")
    print()
    print("1. If intake is incomplete then send SMS saying 'Please complete your intake form'")
    print("2. If no-show risk is high then call patient")
    print("3. If patient speaks spanish then send SMS saying 'Por favor complete su formulario'")
    print("4. If appointment is within 24 hours then send email subject 'Appointment Reminder'")
    print("5. If appointment type contains MRI then call patient saying 'MRI reminder call'")
    print("6. If appointment status is scheduled then send SMS")
    print("7. If location is City1 then send email")
    print("8. If practice contains Ortho then call patient")
    print()
    print("Format: If [condition] then [action]")
    print("Actions: send SMS, send email, call patient")
    print("Add custom messages with: saying 'your message here'")
    print("Add email subjects with: subject 'your subject here'")
    print()

def main():
    """Main interactive function"""
    print("=== Interactive Rules Engine Tester ===")
    print(f"Loading data from: {DATA_DIR}")
    
    # Load data
    practices, patients, appointments, intakes, events = load_json_files()
    if practices is None:
        print("Failed to load data files. Please check the file paths.")
        return
    
    practice_dict, patient_dict, appointment_dict, intake_dict = create_lookups(practices, patients, appointments, intakes)
    
    print(f"\nLoaded:")
    print(f"  - {len(practices)} practices")
    print(f"  - {len(patients)} patients") 
    print(f"  - {len(appointments)} appointments")
    print(f"  - {len(intakes)} intakes")
    
    parser = NLPRuleParser()
    current_time = "2025-09-10T12:00:00Z"
    
    print_examples()
    
    while True:
        try:
            print("\nEnter a rule (or 'examples' to see examples again, 'quit' to exit):")
            rule_input = input("> ").strip()
            
            if rule_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif rule_input.lower() == 'examples':
                print_examples()
                continue
            elif not rule_input:
                continue
            
            # Parse the rule
            rule = parser.parse_rule(rule_input)
            if not rule:
                continue
            
            print(f"\nParsed rule:")
            print(f"  Conditions: {rule['conditions']}")
            print(f"  Actions: {rule['actions']}")
            
            # Process against appointments
            triggered_count = 0
            max_outputs = 10  # Limit output for readability
            
            print(f"\nProcessing rule against appointments...\n")
            
            for appt_id in appointment_dict.keys():
                if triggered_count >= max_outputs:
                    break
                    
                context = build_context(appt_id, current_time, appointment_dict, patient_dict, practice_dict, intake_dict)
                if not context:
                    continue
                
                if evaluate_rule(rule, context):
                    actions = trigger_actions(rule, context)
                    
                    for action in actions:
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
                        
                        triggered_count += 1
                        if triggered_count >= max_outputs:
                            break
            
            if triggered_count == 0:
                print("No appointments matched this rule.")
            elif triggered_count >= max_outputs:
                print(f"... (showing first {max_outputs} matches)")
            
            print(f"\nTotal matches: {triggered_count}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()