"""Linguistic guard to prevent investment advice language."""

import json
import yaml
from pathlib import Path
from typing import List, Tuple, Dict

from src.utils.logger import get_logger

logger = get_logger(__name__)


class LinguisticGuard:
    """Guard against prohibited investment advice language."""
    
    def __init__(self, config_path: str = None):
        """Initialize the linguistic guard."""
        if config_path is None:
            # Default to quality_step_bundle_full location
            config_path = Path(__file__).parent.parent.parent / "quality_step_bundle_full" / "guards" / "LINGUISTIC_GUARD.yaml"
        
        self.banned_words = []
        self.replacements = {}
        self.advice_flags = []
        
        self._load_config(config_path)
    
    def _load_config(self, config_path):
        """Load guard configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.banned_words = config.get('banned', [])
                self.replacements = config.get('replacements', {})
                logger.info(f"Loaded linguistic guard config: {len(self.banned_words)} banned words, {len(self.replacements)} replacements")
        except Exception as e:
            logger.error(f"Failed to load linguistic guard config: {e}")
            # Set defaults
            self.banned_words = ["必ず", "確実に", "絶対に", "今すぐ買う", "今すぐ売る"]
            self.replacements = {"買いましょう": "買う根拠が十分か再検討"}
    
    def check_and_replace(self, text: str) -> Tuple[str, List[str]]:
        """
        Check text for banned words and apply replacements.
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (cleaned_text, advice_flags)
        """
        advice_flags = []
        cleaned_text = text
        
        # Check for banned words
        for banned_word in self.banned_words:
            if banned_word in text:
                advice_flags.append(f"banned:{banned_word}")
                logger.warning(f"Found banned word: {banned_word}")
                # Remove the banned word
                cleaned_text = cleaned_text.replace(banned_word, "")
        
        # Apply replacements
        for original, replacement in self.replacements.items():
            if original in cleaned_text:
                advice_flags.append(f"replaced:{original}")
                cleaned_text = cleaned_text.replace(original, replacement)
                logger.info(f"Replaced '{original}' with '{replacement}'")
        
        return cleaned_text, advice_flags
    
    def check_dict(self, data: Dict) -> Tuple[Dict, List[str]]:
        """
        Recursively check dictionary values for banned words.
        
        Args:
            data: Dictionary to check
            
        Returns:
            Tuple of (cleaned_dict, advice_flags)
        """
        all_flags = []
        cleaned_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                cleaned_value, flags = self.check_and_replace(value)
                cleaned_data[key] = cleaned_value
                all_flags.extend(flags)
            elif isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if isinstance(item, str):
                        cleaned_item, flags = self.check_and_replace(item)
                        cleaned_list.append(cleaned_item)
                        all_flags.extend(flags)
                    else:
                        cleaned_list.append(item)
                cleaned_data[key] = cleaned_list
            elif isinstance(value, dict):
                cleaned_dict, flags = self.check_dict(value)
                cleaned_data[key] = cleaned_dict
                all_flags.extend(flags)
            else:
                cleaned_data[key] = value
        
        return cleaned_data, all_flags