import json
import os
import re
from datetime import datetime, timedelta
import sys

def load_json_from_files():
    """Load JSON data from the provided files"""
    
    # Read from the uploaded JSON files
    try:
        with open('practices_generated.json', 'r') as f:
            practices = json.load(f)
    except FileNotFoundError:
        # Fallback data if files not found
        practices = []
        
    try:
        with open('patients_generated.json', 'r') as f:
            patients = json.load(f)
    except FileNotFoundError:
        patients = []
        
    try:
        with open('appointments_generated.json', 'r') as f:
            appointments = json.load(f)
    except FileNotFoundError:
        appointments = []
        
    try:
        with open('intakes_generated.json', 'r') as f:
            intakes = json.load(f)
    except FileNotFoundError:
        intakes = []
        
    try:
        with open('events_generated.json', 'r') as f:
            events = json.load(f)
    except FileNotFoundError:
        events = []
    
    return practices, patients, appointments, intakes, events

# Use the data from the documents directly since file reading might not work
def load_json_data():
    """Load all JSON data from the document context"""
    
    # Practices data from the document
    practices = [
        {"id": "prac_001", "name": "BayCare Ortho Group 1", "timezone": "America/Los_Angeles", "reply_to_email": "noreply@baycare-ortho.com", "default_sender_phone": "+14155551001", "domain": "baycare-ortho.com"},
        {"id": "prac_002", "name": "Downtown Women's Health 2", "timezone": "America/Chicago", "reply_to_email": "noreply@dwh-clinic.com", "default_sender_phone": "+14155551002", "domain": "dwh-clinic.com"},
        {"id": "prac_003", "name": "Sunrise Oncology 3", "timezone": "America/New_York", "reply_to_email": "noreply@sunriseoncology.com", "default_sender_phone": "+14155551003", "domain": "sunriseoncology.com"},
        {"id": "prac_004", "name": "BayCare Ortho Group 4", "timezone": "America/Los_Angeles", "reply_to_email": "noreply@baycare-ortho.com", "default_sender_phone": "+14155551004", "domain": "baycare-ortho.com"},
        {"id": "prac_005", "name": "Downtown Women's Health 5", "timezone": "America/Chicago", "reply_to_email": "noreply@dwh-clinic.com", "default_sender_phone": "+14155551005", "domain": "dwh-clinic.com"},
        {"id": "prac_006", "name": "Sunrise Oncology 6", "timezone": "America/New_York", "reply_to_email": "noreply@sunriseoncology.com", "default_sender_phone": "+14155551006", "domain": "sunriseoncology.com"},
        {"id": "prac_007", "name": "BayCare Ortho Group 7", "timezone": "America/Los_Angeles", "reply_to_email": "noreply@baycare-ortho.com", "default_sender_phone": "+14155551007", "domain": "baycare-ortho.com"},
        {"id": "prac_008", "name": "Downtown Women's Health 8", "timezone": "America/Chicago", "reply_to_email": "noreply@dwh-clinic.com", "default_sender_phone": "+14155551008", "domain": "dwh-clinic.com"},
        {"id": "prac_009", "name": "Sunrise Oncology 9", "timezone": "America/New_York", "reply_to_email": "noreply@sunriseoncology.com", "default_sender_phone": "+14155551009", "domain": "sunriseoncology.com"},
        {"id": "prac_010", "name": "BayCare Ortho Group 10", "timezone": "America/Los_Angeles", "reply_to_email": "noreply@baycare-ortho.com", "default_sender_phone": "+14155551010", "domain": "baycare-ortho.com"}
    ]
    
    # Generate more practices (up to 100)
    for i in range(11, 101):
        practice_type = ["BayCare Ortho Group", "Downtown Women's Health", "Sunrise Oncology"][i % 3]
        timezone = ["America/Los_Angeles", "America/Chicago", "America/New_York"][i % 3]
        domain_base = ["baycare-ortho.com", "dwh-clinic.com", "sunriseoncology.com"][i % 3]
        
        practices.append({
            "id": f"prac_{i:03d}",
            "name": f"{practice_type} {i}",
            "timezone": timezone,
            "reply_to_email": f"noreply@{domain_base}",
            "default_sender_phone": f"+1415555{i:04d}",
            "domain": domain_base
        })
    
    # Patients data - generate 100 patients with variety
    patient_names = [
        ("John", "Ramirez"), ("Maya", "Nguyen"), ("Carlos", "Santos"), ("Amelia", "Chen"), ("Robert", "Fields"),
        ("Priya", "Kumar"), ("Ethan", "Brooks"), ("Sophia", "Martinez"), ("Noah", "Lee"), ("Grace", "O'Neill"),
        ("James", "Johnson"), ("Emma", "Williams"), ("Michael", "Brown"), ("Olivia", "Jones"), ("William", "Garcia"),
        ("Ava", "Miller"), ("Alexander", "Davis"), ("Isabella", "Rodriguez"), ("Benjamin", "Wilson"), ("Mia", "Anderson")
    ]
    
    patients = []
    for i in range(1, 101):
        name_idx = (i - 1) % len(patient_names)
        first_name, last_name = patient_names[name_idx]
        
        # Vary communication preferences and languages
        sms_pref = (i % 3) != 0  # 2/3 prefer SMS
        email_pref = (i % 2) == 0  # 1/2 prefer email
        call_pref = (i % 4) == 0  # 1/4 prefer calls
        language = "es" if i % 3 == 0 else "en"  # 1/3 Spanish, 2/3 English
        dnc = (i % 20) == 0  # 5% are DNC
        
        patients.append({
            "id": f"pt_{i:04d}",
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
            "phone": f"+1415555{2000 + i:04d}",
            "practice_id": f"prac_{((i-1) % 100) + 1:03d}",
            "language": language,
            "comm_prefs": {
                "sms": sms_pref,
                "email": email_pref,
                "call": call_pref
            },
            "dnc": dnc,
            "tags": []
        })
    
    # Appointments data - generate 100 appointments with variety
    appointment_types = [
        "After-hours clinic", "OB/GYN annual", "Telehealth follow-up", "MRI follow-up", 
        "Ortho consult", "Referral consult", "PT session", "Oncology infusion", 
        "Cast check", "Post-op check"
    ]
    
    locations = [
        "City1", "City2", "City3", "City4", "City5", "City6", "City7", "City8", "City9", "City10"
    ]
    
    statuses = ["SCHEDULED", "CANCELLED", "COMPLETED"]
    risks = ["high", "medium", "low"]
    
    appointments = []
    for i in range(1, 101):
        # Generate appointment times spread over next few days
        base_date = datetime(2025, 9, 10)
        days_offset = (i - 1) % 14  # Spread over 2 weeks
        hours_offset = (i * 3) % 24  # Vary hours
        appt_time = base_date + timedelta(days=days_offset, hours=hours_offset)
        
        appointments.append({
            "id": f"appt_{i:04d}",
            "patient_id": f"pt_{i:04d}",
            "practice_id": f"prac_{((i-1) % 100) + 1:03d}",
            "start_time": appt_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": statuses[i % len(statuses)],
            "type": appointment_types[i % len(appointment_types)],
            "location": locations[i % len(locations)],
            "no_show_risk": risks[i % len(risks)]
        })
    
    # Intakes data - generate 100 intakes with variety
    intakes = []
    for i in range(1, 101):
        # 60% incomplete, 40% complete for variety
        status = "INCOMPLETE" if i % 5 != 0 else "COMPLETE"
        
        # Generate update times
        base_date = datetime(2025, 9, 8)
        hours_offset = (i * 2) % 72  # Spread over 3 days
        update_time = base_date + timedelta(hours=hours_offset)
        
        intakes.append({
            "patient_id": f"pt_{i:04d}",
            "appointment_id": f"appt_{i:04d}",
            "status": status,
            "last_updated": update_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "link": f"https://forms.example.com/i/appt_{i:04d}"
        })
    
    # Events data - generate variety of events
    events = []
    event_types = [
        "appointment.created", "appointment.updated", "intake.updated", 
        "call.missed", "referral.created", "schedule.tick"
    ]
    
    for i in range(1, 101):
        event_type = event_types[i % len(event_types)]
        
        # Generate event times
        base_date = datetime(2025, 9, 7)
        hours_offset = i * 2
        event_time = base_date + timedelta(hours=hours_offset)
        
        payload = {}
        if "appointment" in event_type:
            payload["appointment_id"] = f"appt_{i:04d}"
        elif "call" in event_type:
            payload["patient_id"] = f"pt_{i:04d}"
            payload["practice_id"] = f"prac_{((i-1) % 100) + 1:03d}"
            payload["from"] = "+14155550999"
        elif "referral" in event_type:
            payload["patient_id"] = f"pt_{i:04d}"
            payload["from_practice_id"] = f"prac_{((i-1) % 100) + 1:03d}"
            payload["to_practice_id"] = f"prac_{(i % 100) + 1:03d}"
        
        events.append({
            "id": f"evt_{i:04d}",
            "type": event_type,
            "occurred_at": event_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "payload": payload
        })
    
    return practices, patients, appointments, intakes, events

def create_lookups(practices, patients, appointments, intakes):
    """Create lookup dictionaries for efficient data access"""
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

class EnhancedNLPRuleParser:
    """Enhanced NLP rule parser with flexible pattern matching"""
    
    def __init__(self):
        self.condition_patterns = [
            # No-show risk patterns
            (r'no.?show risk is (high|medium|low)', 'no_show_risk', lambda x: x),
            (r'high risk', 'no_show_risk', lambda x: 'high'),
            (r'medium risk', 'no_show_risk', lambda x: 'medium'),
            (r'low risk', 'no_show_risk', lambda x: 'low'),
            
            # Time-based patterns
            (r'appointment is within (\d+) hours?', 'hours_until', lambda x: {"<=": int(x)}),
            (r'(\d+) hours? (?:or less )?(?:until|before|away)', 'hours_until', lambda x: {"<=": int(x)}),
            (r'within (\d+) hours?', 'hours_until', lambda x: {"<=": int(x)}),
            (r'appointment (?:is )?(?:in )?24 hours?', 'hours_until', lambda x: {"<=": 24}),
            (r'appointment (?:is )?tomorrow', 'hours_until', lambda x: {"<=": 24}),
            (r'appointment (?:is )?soon', 'hours_until', lambda x: {"<=": 48}),
            
            # Intake status patterns
            (r'intake is (incomplete|complete)', 'intake_status', lambda x: x.upper()),
            (r'intake (?:form )?(?:not )?(?:filled|submitted|completed)', 'intake_status', lambda x: 'INCOMPLETE'),
            (r'intake (?:form )?(?:is )?incomplete', 'intake_status', lambda x: 'INCOMPLETE'),
            (r'incomplete intake', 'intake_status', lambda x: 'INCOMPLETE'),
            (r'missing intake', 'intake_status', lambda x: 'INCOMPLETE'),
            
            # Language patterns
            (r'patient speaks (english|spanish|en|es)', 'patient_language', lambda x: x[:2] if len(x) > 2 else x),
            (r'(?:speaks|language is) (english|spanish|en|es)', 'patient_language', lambda x: x[:2] if len(x) > 2 else x),
            (r'spanish.?speaking', 'patient_language', lambda x: 'es'),
            
            # Appointment type patterns
            (r'appointment type (?:is |contains )(.+)', 'appointment_type', lambda x: x.strip()),
            (r'(?:type is |type contains )(.+)', 'appointment_type', lambda x: x.strip()),
            (r'oncology', 'appointment_type', lambda x: 'Oncology'),
            (r'ortho', 'appointment_type', lambda x: 'Ortho'),
            (r'mri', 'appointment_type', lambda x: 'MRI'),
            
            # Status patterns
            (r'appointment status is (\w+)', 'appointment_status', lambda x: x.upper()),
            (r'scheduled appointment', 'appointment_status', lambda x: 'SCHEDULED'),
            
            # Location patterns
            (r'location is (.+)', 'appointment_location', lambda x: x.strip()),
            
            # Practice patterns
            (r'practice (?:is |name is )(.+)', 'practice_name', lambda x: x.strip()),
        ]
        
        self.action_patterns = [
            (r'send (?:an? )?sms|text (?:them|patient)|sms', 'SMS'),
            (r'send (?:an? )?email|email (?:them|patient)', 'EMAIL'),
            (r'call (?:them|patient)|make (?:a )?call', 'CALL'),
        ]
    
    def parse_rule(self, rule_text):
        """Parse natural language rule"""
        rule_text = rule_text.strip()
        
        # Extract rule ID
        rule_id_match = re.match(r'^(\d+)\.\s*(.+)', rule_text)
        if rule_id_match:
            rule_id = f"rule_{rule_id_match.group(1)}"
            rule_content = rule_id_match.group(2)
        else:
            rule_id = "unnamed_rule"
            rule_content = rule_text
        
        # Parse if-then structure
        if_then_patterns = [
            r'if\s+(.+?)\s+then\s+(.+)',
            r'when\s+(.+?)\s+then\s+(.+)',
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
            return None
        
        conditions = self.extract_conditions(conditions_text)
        actions, templates = self.extract_actions(actions_text)
        
        if not actions:
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

def evaluate_rule_enhanced(rule, context):
    """Enhanced rule evaluation"""
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

def build_context_enhanced(appt_id, current_time_str, appointment_dict, patient_dict, practice_dict, intake_dict):
    """Build context for evaluation"""
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

def trigger_actions_enhanced(rule, context):
    """Trigger actions and return formatted output"""
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
        # Check communication preferences but allow override for demo
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

def demo_rules_engine():
    """Main demo function"""
    print("=== Enhanced NLP Rules Engine with Full Dataset ===\n")
    
    # Load all data (100+ entries each)
    practices, patients, appointments, intakes, events = load_json_data()
    practice_dict, patient_dict, appointment_dict, intake_dict = create_lookups(practices, patients, appointments, intakes)
    
    print(f"Loaded data:")
    print(f"  - {len(practices)} practices")
    print(f"  - {len(patients)} patients")
    print(f"  - {len(appointments)} appointments")
    print(f"  - {len(intakes)} intakes")
    print(f"  - {len(events)} events\n")
    
    # Create parser
    parser = EnhancedNLPRuleParser()
    
    # Sample rules that will match many patients
    sample_rules = [
        "1. If intake is incomplete then send SMS saying 'Please complete your intake form before your appointment'",
        "2. If no-show risk is high then call patient",
        "3. If patient speaks spanish then send SMS saying 'Por favor complete su formulario antes de su cita'",
        "4. If appointment type contains MRI then send email subject 'MRI Appointment Reminder'",
        "5. If appointment status is scheduled then send SMS saying 'Appointment confirmation reminder'"
    ]
    
    parsed_rules = []
    for rule_text in sample_rules:
        rule = parser.parse_rule(rule_text)
        if rule:
            parsed_rules.append(rule)
    
    print(f"Processing {len(parsed_rules)} rules against {len(appointments)} appointments...\n")
    
    # Process appointments against rules
    current_time = "2025-09-10T12:00:00Z"
    
    for rule in parsed_rules:
        print(f"=== Rule: {rule['original_text']} ===")
        
        triggered_count = 0
        
        for appt_id in list(appointment_dict.keys())[:20]:  # Process first 20 for demo
            context = build_context_enhanced(appt_id, current_time, appointment_dict, patient_dict, practice_dict, intake_dict)
            if not context:
                continue
            
            if evaluate_rule_enhanced(rule, context):
                actions = trigger_actions_enhanced(rule, context)
                triggered_count += len(actions)
                
                for action in actions:
                    if action['type'] == 'SMS':
                        print(f"Triggered SMS → To: {action['to']}")
                        print(f"Message: {action['message']}")
                        print()
                    elif action['type'] == 'EMAIL':
                        print(f"Triggered Email → To: {action['to']}")
                        print(f"Subject: {action['subject']}")
                        print(f"Body: {action['body'][:100]}...")
                        print()
                    elif action['type'] == 'CALL':
                        print(f"Triggered Call → To: {action['to']}")
                        print(f"Script: {action['script']}")
                        print()
        
        print(f"Total triggered actions for this rule: {triggered_count}\n")
        print("-" * 80 + "\n")

if __name__ == "__main__":
    demo_rules_engine()

