"""
Script de prueba para el endpoint de resumen conversacional.
"""
import requests
import pandas as pd
import json
from datetime import datetime, timezone

PARQUET_PATH = "../data/reto.parquet"
RESUMEN_ENDPOINT = "http://localhost:8000/api/v1/analysis/resumen"


def load_dataset(path: str = PARQUET_PATH) -> pd.DataFrame:
    """Carga el dataset desde el archivo parquet."""
    return pd.read_parquet(path)


def get_thread_messages(df: pd.DataFrame, thread_id: str) -> list:
    """
    Obtiene todos los mensajes de un thread y los formatea para el endpoint.
    
    Args:
        df: DataFrame con todos los datos
        thread_id: ID del thread
        
    Returns:
        Lista de mensajes formateados
    """
    thread_df = df[df["threadId"] == thread_id].copy()
    
    if thread_df.empty:
        return []
    
    # Ordenar por createdAt
    if thread_df['createdAt'].dtype == 'object':
        thread_df['createdAt'] = pd.to_numeric(thread_df['createdAt'], errors='coerce')
    
    thread_df = thread_df.sort_values('createdAt', na_position='last')
    
    # Formatear mensajes
    messages = []
    for _, row in thread_df.iterrows():
        created_at = None
        if pd.notna(row.get('createdAt')):
            try:
                ts = int(row['createdAt']) / 1000
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                created_at = dt.isoformat()
            except:
                pass
        
        messages.append({
            "id": str(row["id"]),
            "text": row.get("text") if pd.notna(row.get("text")) else "",
            "createdAt": created_at,
            "author": row.get("author") if pd.notna(row.get("author")) else None
        })
    
    return messages


def test_resumen_endpoint(thread_id: str):
    """
    Prueba el endpoint de resumen con un thread específico.
    
    Args:
        thread_id: ID del thread a analizar
    """
    df = load_dataset()
    
    print(f"[INFO] Dataset cargado: {len(df)} registros")
    print(f"[INFO] Analizando thread: {thread_id}\n")
    
    # Obtener mensajes del thread
    messages = get_thread_messages(df, thread_id)
    
    if not messages:
        print(f"[ERROR] No se encontraron mensajes para el thread {thread_id}")
        return
    
    print(f"[INFO] Mensajes encontrados: {len(messages)}")
    print(f"[INFO] Primer mensaje: {messages[0]['text'][:100]}...")
    print(f"[INFO] Último mensaje: {messages[-1]['text'][:100]}...\n")
    
    # Construir payload
    payload = {
        "threadId": thread_id,
        "messages": messages
    }
    
    print(f"[INFO] Enviando request al endpoint...")
    print(f"[INFO] URL: {RESUMEN_ENDPOINT}")
    print(f"[INFO] Payload size: {len(json.dumps(payload))} bytes\n")
    
    try:
        response = requests.post(RESUMEN_ENDPOINT, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        print("\n" + "="*80)
        print("RESUMEN CONVERSACIONAL")
        print("="*80)
        
        print(f"\n📋 Thread ID: {data['threadId']}")
        print(f"📊 Mensajes analizados: {data['message_count']}")
        
        print(f"\n📝 RESUMEN:")
        print(data['resumen'])
        
        print(f"\n🔑 TEMAS CLAVE:")
        for i, tema in enumerate(data['temas_clave'], 1):
            print(f"  {i}. {tema}")
        
        print(f"\n💭 POSTURAS DETECTADAS:")
        for i, postura in enumerate(data['posturas'], 1):
            print(f"  {i}. {postura}")
        
        print(f"\n😊 TONO EMOCIONAL:")
        print(f"  {data['tono_emocional']}")
        
        print(f"\n⚠️  RIESGOS DETECTADOS:")
        if data['riesgos_detectados']:
            for i, riesgo in enumerate(data['riesgos_detectados'], 1):
                print(f"  {i}. {riesgo}")
        else:
            print("  Ninguno")
        
        print(f"\n✅ CONCLUSIÓN:")
        print(f"  {data['conclusion']}")
        
        print("\n" + "="*80)
        
    except requests.exceptions.Timeout:
        print("[ERROR] Timeout al llamar al endpoint (120s)")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTP Error: {e}")
        if e.response is not None:
            print(f"[ERROR] Response: {e.response.text}")
    except Exception as e:
        print(f"[ERROR] Error inesperado: {str(e)}")


if __name__ == "__main__":
    df = load_dataset()
    
    # Elegir un thread con varios mensajes
    thread_counts = df.groupby("threadId").size().sort_values(ascending=False)
    
    print("\n📊 Top 10 threads más activos:")
    for i, (thread_id, count) in enumerate(thread_counts.head(10).items(), 1):
        print(f"  {i}. Thread {thread_id}: {count} mensajes")
    
    # Usar el tercer thread más activo (para evitar el spam del primero)
    selected_thread = thread_counts.index[2]
    
    print(f"\n[INFO] Thread seleccionado: {selected_thread}")
    print(f"[INFO] Mensajes: {thread_counts[selected_thread]}\n")
    
    test_resumen_endpoint(selected_thread)
