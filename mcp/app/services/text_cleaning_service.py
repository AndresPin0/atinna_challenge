"""
Servicio de limpieza y normalización de texto conversacional.
"""
import re
from typing import List
from app.models.resumen_models import MessageInput


class TextCleaningService:
    """Servicio para limpiar y normalizar texto de conversaciones."""
    
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
        
        # Convertir entidades numéricas
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
        
        # Reemplazar múltiples espacios/tabs/newlines por un solo espacio
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar espacios al inicio y final
        text = text.strip()
        
        return text
    
    @staticmethod
    def clean_urls(text: str) -> str:
        """
        Limpia URLs del texto.
        
        Args:
            text: Texto con URLs
            
        Returns:
            Texto sin URLs completas
        """
        if not text:
            return ""
        
        # Remover URLs completas
        url_pattern = r'https?://[^\s]+'
        text = re.sub(url_pattern, '', text)
        
        return text
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Limpia un texto individual aplicando todas las transformaciones.
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        if not text:
            return ""
        
        cleaned = text
        cleaned = TextCleaningService.clean_html_entities(cleaned)
        cleaned = TextCleaningService.clean_urls(cleaned)
        cleaned = TextCleaningService.normalize_whitespace(cleaned)
        
        return cleaned
    
    @staticmethod
    def build_conversation_text(messages: List[MessageInput]) -> str:
        """
        Construye el texto de conversación completo desde una lista de mensajes.
        
        Args:
            messages: Lista de mensajes
            
        Returns:
            Texto completo de la conversación limpio
        """
        if not messages:
            return ""
        
        conversation_parts = []
        
        for msg in messages:
            if msg.text and msg.text.strip():
                cleaned_text = TextCleaningService.clean_text(msg.text)
                if cleaned_text:
                    conversation_parts.append(cleaned_text)
        
        conversation = "\n\n".join(conversation_parts)
        
        return conversation
    
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
            # Buscar el último espacio para no cortar palabras
            last_space = truncated.rfind(' ')
            if last_space > 0:
                truncated = truncated[:last_space]
            return truncated + '\n\n[... conversación truncada por longitud ...]'
        
        return text
