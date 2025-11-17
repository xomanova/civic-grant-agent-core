"""
Session Manager
Manages department profile state across agents (demonstrates ADK session/memory requirement).
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages session state and memory for the agent system.
    This demonstrates the ADK requirement for session & memory management.
    """

    def __init__(self, config_path: str = "department_config.json"):
        """
        Initialize the session manager.

        Args:
            config_path: Path to department configuration file
        """
        self.config_path = Path(config_path)
        self.department_profile: Optional[Dict[str, Any]] = None
        self.session_data: Dict[str, Any] = {
            "session_id": self._generate_session_id(),
            "created_at": datetime.now().isoformat(),
            "agent_interactions": [],
            "context": {}
        }

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def load_department_profile(self) -> Dict[str, Any]:
        """
        Load department profile from configuration file.

        Returns:
            Department profile dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid JSON
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Department configuration not found: {self.config_path}\n"
                f"Please create {self.config_path} with your department information."
            )

        try:
            with open(self.config_path, 'r') as f:
                self.department_profile = json.load(f)
            
            logger.info(f"Loaded department profile: {self.department_profile.get('name')}")
            
            # Store in session context
            self.session_data["context"]["department_profile"] = self.department_profile
            
            return self.department_profile

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")

    def get_department_profile(self) -> Dict[str, Any]:
        """
        Get current department profile.

        Returns:
            Department profile dictionary

        Raises:
            RuntimeError: If profile hasn't been loaded yet
        """
        if self.department_profile is None:
            raise RuntimeError(
                "Department profile not loaded. Call load_department_profile() first."
            )
        return self.department_profile

    def update_context(self, key: str, value: Any) -> None:
        """
        Update session context with new information.

        Args:
            key: Context key
            value: Context value
        """
        self.session_data["context"][key] = value
        logger.debug(f"Updated session context: {key}")

    def get_context(self, key: str, default: Any = None) -> Any:
        """
        Get value from session context.

        Args:
            key: Context key
            default: Default value if key doesn't exist

        Returns:
            Context value or default
        """
        return self.session_data["context"].get(key, default)

    def log_agent_interaction(
        self,
        agent_name: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an agent interaction to session history.

        Args:
            agent_name: Name of the agent
            action: Action performed
            details: Optional additional details
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action": action,
            "details": details or {}
        }
        self.session_data["agent_interactions"].append(interaction)
        logger.info(f"[{agent_name}] {action}")

    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get summary of current session.

        Returns:
            Dictionary with session statistics
        """
        return {
            "session_id": self.session_data["session_id"],
            "created_at": self.session_data["created_at"],
            "department": self.department_profile.get("name") if self.department_profile else None,
            "total_interactions": len(self.session_data["agent_interactions"]),
            "agents_used": list(set(
                i["agent"] for i in self.session_data["agent_interactions"]
            ))
        }

    def save_session(self, output_dir: str = "output") -> Path:
        """
        Save session data to file.

        Args:
            output_dir: Directory to save session file

        Returns:
            Path to saved session file
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        session_file = output_path / f"{self.session_data['session_id']}.json"
        
        with open(session_file, 'w') as f:
            json.dump(self.session_data, f, indent=2)
        
        logger.info(f"Session saved to {session_file}")
        return session_file

    def get_full_session_data(self) -> Dict[str, Any]:
        """
        Get complete session data.

        Returns:
            Full session data dictionary
        """
        return self.session_data
