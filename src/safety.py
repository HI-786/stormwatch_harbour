import re

class SafetyController:
    def __init__(self):
        # Restricted actions requiring human approval (Task E1)
        self.restricted_actions = ["close_harbour", "release_cargo"]

    def sanitize_input(self, text_input):
        """
        Task D2: XML Data Isolation & Injection Defense
        Encloses untrusted text inside data tags to prevent prompt injection.
        """
        sanitized = re.sub(r'(?i)ignore (previous|all) instructions', '[FILTERED]', text_input)
        return f"<untrusted_data>\n{sanitized}\n</untrusted_data>"

    def check_approval_gate(self, action_name, user_override=None):
        """
        Task E1: Human-in-the-Loop Approval Gate
        Intercepts high-risk actions and requires human sign-off.
        """
        if action_name in self.restricted_actions:
            if user_override is not None:
                return user_override
            
            print(f"\n[APPROVAL GATE TRIGGERED]: Action '{action_name}' requires human authorization.")
            response = input("Approve execution? (y/n): ").strip().lower()
            return response == 'y'
            
        return True  # Low-risk actions auto-approve