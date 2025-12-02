"""
Módulo de limpieza y normalización de texto conversacional.
"""
import re
from typing import Optional


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
        
        cleaned = TextCleaner.clean_html_entities(conversation)
        
        cleaned = TextCleaner.normalize_whitespace(cleaned)
        
        return cleaned
    
    @staticmethod
    def truncate_if_needed(text: str, max_length: int = 100000) -> str:
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
        
        if len(text) > max_length:
            truncated = text[:max_length]
            last_space = truncated.rfind(' ')
            if last_space > 0:
                truncated = truncated[:last_space]
            return truncated + "\n\n[... conversación truncada por longitud ...]"
        
        return text

