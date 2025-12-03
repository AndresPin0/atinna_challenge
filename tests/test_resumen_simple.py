"""
Test simple para el endpoint de resumen conversacional.
Carga una conversación real del dataset y la envía al endpoint.
"""
import requests
import json
import pandas as pd

RESUMEN_ENDPOINT = "http://localhost:8000/api/v1/analysis/resumen"
PARQUET_PATH = "data/Reto_data.parquet"


def load_real_conversation():
    """Carga una conversación real del dataset."""
    print("Cargando dataset...")
    df = pd.read_parquet(PARQUET_PATH, engine='fastparquet')
    
    # Encontrar el thread más activo
    thread_counts = df.groupby("threadId").size().sort_values(ascending=False)
    top_thread_id = thread_counts.index[0]
    
    print(f"Thread más activo: {top_thread_id} con {thread_counts.iloc[0]} mensajes")
    
    # Tomar el thread y ordenar por fecha
    df_thread = df[df["threadId"] == top_thread_id].copy()
    df_thread = df_thread.sort_values("createdAt")
    
    # Tomar los primeros 8 mensajes
    messages_sample = df_thread.head(8)
    
    messages = []
    for _, row in messages_sample.iterrows():
        text = str(row.get('text', '')) if pd.notna(row.get('text')) else ''
        author = str(row.get('author', 'Anónimo')) if pd.notna(row.get('author')) else 'Anónimo'
        created = pd.to_datetime(row['createdAt'], unit='ms', utc=True).isoformat()
        msg_id = str(row['id'])
        
        messages.append({
            "id": msg_id,
            "text": text,
            "createdAt": created,
            "author": author
        })
    
    return {
        "threadId": str(top_thread_id),
        "messages": messages
    }


def test_resumen_simple():
    """Prueba básica con conversación real del dataset."""
    
    payload = load_real_conversation()
    
    print("=" * 80)
    print("TEST: Endpoint de Resumen Conversacional")
    print("=" * 80)
    print(f"\nEndpoint: {RESUMEN_ENDPOINT}")
    print(f"Thread ID: {payload['threadId']}")
    print(f"Mensajes a analizar: {len(payload['messages'])}")
    
    print("\nConversación:")
    for msg in payload['messages']:
        print(f"\n  [{msg['author']}]")
        print(f"  {msg['text'][:100]}...")
    
    print(f"\n\nEnviando request al endpoint...")
    
    try:
        response = requests.post(RESUMEN_ENDPOINT, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        print("\n" + "=" * 80)
        print("RESPUESTA EXITOSA")
        print("=" * 80)
        
        print(f"\nThread ID: {data['threadId']}")
        print(f"Mensajes analizados: {data['message_count']}")
        
        print(f"\n" + "─" * 80)
        print("RESUMEN EJECUTIVO")
        print("─" * 80)
        print(data['resumen'])
        
        print(f"\n" + "─" * 80)
        print("TEMAS CLAVE")
        print("─" * 80)
        for i, tema in enumerate(data['temas_clave'], 1):
            print(f"  {i}. {tema}")
        
        print(f"\n" + "─" * 80)
        print("POSTURAS DETECTADAS")
        print("─" * 80)
        for i, postura in enumerate(data['posturas'], 1):
            print(f"  {i}. {postura}")
        
        print(f"\n" + "─" * 80)
        print("TONO EMOCIONAL")
        print("─" * 80)
        print(f"  {data['tono_emocional']}")
        
        print(f"\n" + "─" * 80)
        print("RIESGOS DETECTADOS")
        print("─" * 80)
        if data['riesgos_detectados']:
            for i, riesgo in enumerate(data['riesgos_detectados'], 1):
                print(f"  {i}. {riesgo}")
        else:
            print("  Ningún riesgo detectado")
        
        print(f"\n" + "─" * 80)
        print("CONCLUSIÓN")
        print("─" * 80)
        print(f"  {data['conclusion']}")
        
        print("\n" + "=" * 80)
        print("TEST COMPLETADO EXITOSAMENTE")
        print("=" * 80)
        
        return True
        
    except requests.exceptions.Timeout:
        print("\nERROR: Timeout al llamar al endpoint (120s)")
        return False
    except requests.exceptions.ConnectionError:
        print("\nERROR: No se pudo conectar al servidor")
        print("   Verifica que el servidor esté corriendo en http://localhost:8000")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"\nERROR HTTP: {e}")
        if e.response is not None:
            print(f"\nDetalle del error:")
            try:
                error_data = e.response.json()
                print(json.dumps(error_data, indent=2))
            except:
                print(e.response.text)
        return False
    except Exception as e:
        print(f"\nERROR INESPERADO: {str(e)}")
        return False


if __name__ == "__main__":
    print("\nIniciando test del endpoint de resumen...\n")
    success = test_resumen_simple()
    
    if success:
        print("\nEl endpoint de resumen está funcionando correctamente!")
    else:
        print("\nEl test ha fallado. Revisa los errores arriba.")
