"""
Módulo de limpieza y normalización de texto conversacional.
"""
import re
from typing import Optional
from .config import TextProcessingConfig


class TextCleaner:
    """Limpieza de texto para conversaciones digitales."""
    
    @staticmethod
    def clean_html_entities(text: str) -> str:
        """
        Limpia entidades HTML codificadas.
        
        Args:
            text: Texto con entidades HTML
            
        Returns:
            Texto limpio
        """
        if not text:
            return ""
        
        # Reemplazar entidades HTML comunes
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
        Normaliza espacios en blanco.
        
        Args:
            text: Texto con espacios irregulares
            
        Returns:
            Texto con espacios normalizados
        """
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text)
        
        text = text.strip()
        
        return text
    
    @staticmethod
    def clean_urls(text: str) -> str:
        """
        Limpia URLs del texto, dejando solo el dominio.
        
        Args:
            text: Texto con URLs
            
        Returns:
            Texto sin URLs completas
        """
        if not text:
            return ""
        
        url_pattern = r'https?://[^\s]+'
        text = re.sub(url_pattern, '', text)
        
        return text
    
    @staticmethod
    def clean_conversation(conversation: str) -> str:
        """
        Limpia una conversación completa aplicando todas las transformaciones.
        
        Args:
            conversation: Texto de la conversación
            
        Returns:
            Conversación limpia
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
        Trunca texto si excede longitud máxima (para evitar límites de API).
        
        Args:
            text: Texto a truncar
            max_length: Longitud máxima permitida 
            
        Returns:
            Texto truncado si es necesario
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

