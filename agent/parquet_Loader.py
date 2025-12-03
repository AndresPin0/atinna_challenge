# agent/parquet_loader.py (nuevo archivo)
"""
Loader para cargar mensajes desde Parquet en el agente.
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Any
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

    def load_propagation_messages(self, root_id: str) -> List[Dict[str, Any]]:
        """
        Carga todos los mensajes del thread asociado a un root_id,
        en el formato esperado por el MCP de propagación.
        """
        import math

        df = pd.read_parquet(self.parquet_path)

        row = df[df["id"] == root_id]
        if row.empty:
            raise ValueError(f"No existe mensaje con id={root_id} en el dataset")
        row = row.iloc[0]

        thread_id = row["threadId"]
        df_thread = df[df["threadId"] == thread_id].copy()

        def epoch_ms_to_iso(value):
            """Convert epoch milliseconds (possibly as string) to ISO-8601, safely."""
            if pd.isna(value):
                return None
            try:
                numeric = pd.to_numeric(value, errors="coerce")
                if pd.isna(numeric):
                    return None
                return pd.to_datetime(numeric, unit="ms", utc=True).isoformat()
            except Exception:
                return None

        def safe_float(value) -> float:
            if value is None or (isinstance(value, float) and math.isnan(value)):
                return 0.0
            try:
                return float(value)
            except Exception:
                return 0.0

        def parse_bool(value):
            if isinstance(value, bool):
                return value
            if value is None:
                return None
            s = str(value).strip().lower()
            if s in {"true", "1", "t", "yes", "y"}:
                return True
            if s in {"false", "0", "f", "no", "n"}:
                return False
            return None

        messages: List[Dict[str, Any]] = []
        for _, r in df_thread.iterrows():
            author_id = (
                str(r.get("authorId"))
                if pd.notna(r.get("authorId")) and str(r.get("authorId")).strip() != ""
                else None
            )
            parent_raw = r.get("parentId")
            parent_id = (
                str(parent_raw)
                if pd.notna(parent_raw) and str(parent_raw).strip() != ""
                else None
            )

            messages.append(
                {
                    "id": str(r["id"]),
                    "parentId": parent_id,
                    "threadId": str(r.get("threadId")) if r.get("threadId") is not None else None,
                    "authorId": author_id,
                    "createdAt": epoch_ms_to_iso(r.get("createdAt")),
                    "text": r.get("text") if pd.notna(r.get("text")) else None,
                    "isComment": parse_bool(r.get("isComment")) if "isComment" in r else None,
                    "isRetweet": parse_bool(r.get("isRetweet")) if "isRetweet" in r else None,
                    "engagementRate": safe_float(r.get("engagementRate")),
                    "influenceScore": safe_float(r.get("influenceScore")),
                }
            )

        return messages