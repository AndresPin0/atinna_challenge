"""
Module for cleaning and normalizing conversational text.
"""
import re
from typing import Optional
from .config import TextProcessingConfig


class TextCleaner:
    """Cleaning text for digital conversations."""
    
    @staticmethod
    def clean_html_entities(text: str) -> str:
        """
        Cleans encoded HTML entities.
        
        Args:
            text: Text with HTML entities
            
        Returns:
            Clean text
        """
        if not text:
            return ""
        
        # Replace common HTML entities
        replacements = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&apos;': "'",
            '&oacute;': 'ó',
            '&aacute;': 'á',
            '&eacute;': 'é',
            '&iacute;': 'í',
            '&uacute;': 'ú',
            '&ntilde;': 'ñ',
            '&Oacute;': 'Ó',
            '&Aacute;': 'Á',
            '&Eacute;': 'É',
            '&Iacute;': 'Í',
            '&Uacute;': 'Ú',
            '&Ntilde;': 'Ñ',
            '&ldquo;': '"',
            '&rdquo;': '"',
            '&lsquo;': "'",
            '&rsquo;': "'",
            '&hellip;': '...',
            '&ndash;': '-',
            '&mdash;': '-',
        }
        
        for entity, replacement in replacements.items():
            text = text.replace(entity, replacement)
        
        text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
        text = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), text)
        
        return text
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalizes whitespace.
        
        Args:
            text: Text with irregular whitespace
            
        Returns:
            Text with normalized whitespace
        """
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text)
        
        text = text.strip()
        
        return text
    
    @staticmethod
    def clean_urls(text: str) -> str:
        """
        Cleans URLs from text, leaving only the domain.
        
        Args:
            text: Text with URLs
            
        Returns:
            Text without full URLs
        """
        if not text:
            return ""
        
        url_pattern = r'https?://[^\s]+'
        text = re.sub(url_pattern, '', text)
        
        return text
    
    @staticmethod
    def clean_conversation(conversation: str) -> str:
        """
        Cleans a complete conversation applying all transformations.
        
        Args:
            conversation: Text of the conversation
            
        Returns:
            Clean conversation
        """
        if not conversation:
            return ""
        
        cleaned = conversation
        
        if TextProcessingConfig.CLEAN_HTML_ENTITIES:
            cleaned = TextCleaner.clean_html_entities(cleaned)
        
        if TextProcessingConfig.CLEAN_URLS:
            cleaned = TextCleaner.clean_urls(cleaned)
        
        if TextProcessingConfig.NORMALIZE_WHITESPACE:
            cleaned = TextCleaner.normalize_whitespace(cleaned)
        
        return cleaned
    
    @staticmethod
    def truncate_if_needed(text: str, max_length: Optional[int] = None) -> str:
        """
        Truncates text if it exceeds the maximum length (to avoid API limits).
        
        Args:
            text: Text to truncate
            max_length: Maximum length allowed
            
        Returns:
            Truncated text if needed
        """
        if not text:
            return ""
        
        max_length = max_length or TextProcessingConfig.MAX_CONVERSATION_LENGTH
        
        if len(text) > max_length:
            truncated = text[:max_length]
            last_space = truncated.rfind(' ')
            if last_space > 0:
                truncated = truncated[:last_space]
            return truncated + TextProcessingConfig.TRUNCATE_MESSAGE
        
        return text

