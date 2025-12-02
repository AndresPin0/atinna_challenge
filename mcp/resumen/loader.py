"""
Loader para cargar y filtrar conversaciones desde archivo Parquet.
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import os


class ParquetLoader:
    """Carga y filtra conversaciones desde archivo Parquet."""
    
    def __init__(self, parquet_path: str):
        """
        Inicializa el loader con la ruta al archivo Parquet.
        
        Args:
            parquet_path: Ruta al archivo .parquet
        """
        self.parquet_path = Path(parquet_path)
        if not self.parquet_path.exists():
            raise FileNotFoundError(f"Archivo Parquet no encontrado: {parquet_path}")
    
    def load_thread(self, thread_id: str) -> pd.DataFrame:
        """
        Carga y filtra mensajes por threadId.
        
        Args:
            thread_id: ID del thread a cargar
            
        Returns:
            DataFrame con los mensajes del thread, ordenados por createdAt
        """
        df = pd.read_parquet(self.parquet_path)
        
        thread_df = df[df['threadId'] == thread_id].copy()
        
        if thread_df.empty:
            return pd.DataFrame()
        
        if thread_df['createdAt'].dtype == 'object':
            thread_df['createdAt'] = pd.to_numeric(thread_df['createdAt'], errors='coerce')
        
        thread_df = thread_df.sort_values('createdAt', na_position='last')
        
        return thread_df
    
    def get_conversation_text(self, thread_id: str) -> str:
        """
        Obtiene el texto completo de la conversación uniendo todos los mensajes.
        
        Args:
            thread_id: ID del thread
            
        Returns:
            String con todos los textos unidos
        """
        df = self.load_thread(thread_id)
        
        if df.empty:
            return ""
        
        texts = df['text'].dropna().astype(str)
        
        conversation = "\n\n".join(texts.tolist())
        
        return conversation
    
    def get_thread_metadata(self, thread_id: str) -> Dict:
        """
        Obtiene metadatos del thread.
        
        Args:
            thread_id: ID del thread
            
        Returns:
            Diccionario con metadatos
        """
        df = self.load_thread(thread_id)
        
        if df.empty:
            return {
                "threadId": thread_id,
                "message_count": 0,
                "first_message": None,
                "last_message": None
            }
        
        return {
            "threadId": thread_id,
            "message_count": len(df),
            "first_message": str(df['createdAt'].min()) if not df['createdAt'].isna().all() else None,
            "last_message": str(df['createdAt'].max()) if not df['createdAt'].isna().all() else None
        }

