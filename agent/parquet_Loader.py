# agent/parquet_loader.py (nuevo archivo)
"""
Loader para cargar mensajes desde Parquet en el agente.
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
from .config import AgentConfig


class AgentParquetLoader:
    """Carga mensajes desde Parquet para el agente."""
    
    def __init__(self, parquet_path: Optional[str] = None):
        """
        Inicializa el loader.
        
        Args:
            parquet_path: Ruta al archivo Parquet. Si None, usa AgentConfig.get_parquet_path()
        """
        self.parquet_path = Path(parquet_path or AgentConfig.get_parquet_path())
        if not self.parquet_path.exists():
            raise FileNotFoundError(f"Parquet file not found: {self.parquet_path}")
    
    def load_thread_messages(self, thread_id: str) -> List[Dict[str, str]]:
        """
        Carga mensajes de un thread desde Parquet.
        
        Args:
            thread_id: ID del thread a cargar
            
        Returns:
            Lista de diccionarios con formato MessageInput para el endpoint MCP
        """
        df = pd.read_parquet(self.parquet_path)
        
        thread_df = df[df['threadId'] == thread_id].copy()
        
        if thread_df.empty:
            raise ValueError(f"Thread {thread_id} no encontrado en Parquet")
        
        # Ordenar por fecha
        if thread_df['createdAt'].dtype == 'object':
            thread_df['createdAt'] = pd.to_numeric(thread_df['createdAt'], errors='coerce')
        thread_df = thread_df.sort_values('createdAt', na_position='last')
        
        # Convertir a formato MessageInput
        messages = []
        for _, row in thread_df.iterrows():
            msg = {
                "id": str(row.get('id', '')),
                "text": str(row.get('text', '')) if pd.notna(row.get('text')) else None,
            }
            
            # createdAt
            if pd.notna(row.get('createdAt')):
                created_at = row.get('createdAt')
                # Si es numérico (timestamp), convertir a ISO string
                if isinstance(created_at, (int, float)):
                    msg["createdAt"] = pd.to_datetime(created_at, unit='ms', utc=True).isoformat()
                else:
                    msg["createdAt"] = str(created_at)
            else:
                msg["createdAt"] = None
            
            # author
            if pd.notna(row.get('author')):
                msg["author"] = str(row.get('author', ''))
            else:
                msg["author"] = None
            
            messages.append(msg)
        
        return messages