from abc import ABC, abstractmethod

class BaseWatcherAgent(ABC):
    @abstractmethod
    def fetch(self, url: str) -> dict:
        """
        Returns: {
            url: str,
            title: str,
            source: str,  # e.g. "RBI", "SEBI", "MCA"
            text: str
        }
        """
        pass

class BaseDedupAgent(ABC):
    @abstractmethod
    def is_duplicate(self, doc: dict, db) -> bool:
        """
        Returns: True if circular already exists in DB, False if new
        """
        pass

class BaseMAPExtractor(ABC):
    @abstractmethod
    def extract(self, doc: dict) -> dict:
        """
        Returns: {
            maps: [{ action: str, confidence: float }],
            confidence: float  # overall confidence score
        }
        """
        pass

class BaseRouterAgent(ABC):
    @abstractmethod
    def assign(self, map_item: dict) -> dict:
        """
        Returns: {
            department: str,
            sla_days: int
        }
        """
        pass

class BaseNotifierAgent(ABC):
    @abstractmethod
    def dispatch(self, map_item: dict, owner: dict):
        """
        Sends notification to assigned department
        """
        pass

class BaseValidatorAgent(ABC):
    @abstractmethod
    def validate(self, map_id: int, evidence: dict, db) -> dict:
        """
        Returns: {
            status: str,           # "complete" or "incomplete"
            missing_items: list,   # list of missing requirements, empty if complete
        }
        """
        pass