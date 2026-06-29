from app.agents.base import BaseValidatorAgent
from app.db.models import Evidence, MAPItem
from datetime import datetime

class ValidatorConfig:
    def __init__(self, min_description_len=50):
        self.min_description_len = min_description_len

class ValidatorAgent(BaseValidatorAgent):
    """
    Validates evidence submitted by departments against the original MAP.
    Supports both:
    1. Signature A: validate(map_id: int, evidence: dict, db) -> dict
    2. Signature B: validate(description: str, file_url: str) -> ValidationResult
    """

    def __init__(self, config=None):
        self.config = config or ValidatorConfig()

    def validate(self, *args, **kwargs):
        is_signature_a = False
        if len(args) >= 1 and isinstance(args[0], (int, float)):
            is_signature_a = True
        elif 'map_id' in kwargs or 'db' in kwargs or 'evidence' in kwargs:
            is_signature_a = True

        if is_signature_a:
            map_id = args[0] if len(args) > 0 else kwargs.get('map_id')
            evidence = args[1] if len(args) > 1 else kwargs.get('evidence', {})
            db = args[2] if len(args) > 2 else kwargs.get('db')

            map_item = db.query(MAPItem).filter(MAPItem.id == map_id).first()
            if not map_item:
                return {"status": "incomplete", "missing_items": ["MAP not found"]}

            missing_items = []
            description = evidence.get("description", "").strip()
            min_len = getattr(self.config, 'min_description_len', 20)
            if len(description) < min_len:
                missing_items.append("detailed description of action taken")

            if not evidence.get("file_url"):
                missing_items.append("supporting document/file")

            if missing_items:
                return {"status": "incomplete", "missing_items": missing_items}
            return {"status": "complete", "missing_items": []}

        else:
            description = args[0] if len(args) > 0 else kwargs.get('description', '')
            file_url = args[1] if len(args) > 1 else kwargs.get('file_url', '')

            is_valid = True
            feedback = "Evidence looks good."

            min_len = getattr(self.config, 'min_description_len', 50)
            if not description or len(description.strip()) < min_len:
                is_valid = False
                feedback = f"Description is too short (minimum {min_len} characters required)."
            elif not file_url or not file_url.startswith("http"):
                is_valid = False
                feedback = "Please provide a valid supporting document URL."

            class ValidationResult:
                def __init__(self, is_valid, feedback):
                    self.is_valid = is_valid
                    self.feedback = feedback

            return ValidationResult(is_valid, feedback)