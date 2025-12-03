"""
Loader for loading and filtering conversations from a Parquet file.
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import os


class ParquetLoader:
    """Loads and filters conversations from a Parquet file."""
    
    def __init__(self, parquet_path: str):
        """
        Initializes the loader with the path to the Parquet file.
        
        Args:
            parquet_path: Path to the .parquet file
        """
        self.parquet_path = Path(parquet_path)
        if not self.parquet_path.exists():
            raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    def load_thread(self, thread_id: str) -> pd.DataFrame:
        """
        Loads and filters messages by threadId.
        
        Args:
            thread_id: ID of the thread to load
            
        Returns:
            DataFrame with the messages of the thread, ordered by createdAt
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
        Gets the complete text of the conversation by joining all messages.
        
        Args:
            thread_id: ID of the thread
            
        Returns:
            String with all texts joined
        """
        df = self.load_thread(thread_id)
        
        if df.empty:
            return ""
        
        texts = df['text'].dropna().astype(str)
        
        conversation = "\n\n".join(texts.tolist())
        
        return conversation
    
    def get_thread_metadata(self, thread_id: str) -> Dict:
        """
        Gets metadata of the thread.
        
        Args:
            thread_id: ID of the thread
            
        Returns:
            Dictionary with metadata
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

