"""
Script de prueba para analizar el sentimiento de registros específicos.
"""
import pandas as pd
import requests
from pathlib import Path
from typing import Dict, Any

# Configuración
PARQUET_PATH = "data/Reto_data.parquet"
SENTIMENT_ENDPOINT = "http://localhost:8000/api/v1/analysis/sentiment"


def build_text_from_row(row: Dict[str, Any]) -> str:
    """Construye el texto combinando varios campos del registro."""
    parts = []
    
    if row.get("text"):
        parts.append(str(row["text"]))
    if row.get("title"):
        parts.append(f"Título: {row['title']}")
    if row.get("description"):
        parts.append(f"Descripción: {row['description']}")
    if row.get("caption"):
        parts.append(f"Caption: {row['caption']}")
    if row.get("parentText"):
        parts.append(f"Comentario padre: {row['parentText']}")
    
    if not parts:
        return "(sin texto disponible)"
    
    return "\n".join(parts)


def analyze_single_message(df: pd.DataFrame, post_id: str) -> None:
    """Analiza el sentimiento de un mensaje específico."""
    
    # Buscar el registro
    row = df[df["id"] == post_id]
    if row.empty:
        print(f"No se encontró ningún post con id={post_id}")
        return
    
    row = row.iloc[0].to_dict()
    
    print(f"\n{'='*80}")
    print(f"Analizando sentimiento del mensaje: {post_id}")
    print(f"{'='*80}")
    
    # Mostrar información del post
    print(f"\nInformación del Post:")
    print(f"  - ID: {row.get('id')}")
    print(f"  - Autor: {row.get('author', 'N/A')}")
    print(f"  - Tipo: {row.get('type', 'N/A')}")
    print(f"  - Fuente: {row.get('sourceName', 'N/A')}")
    print(f"  - Fecha: {row.get('createdAt', 'N/A')}")
    
    # Construir texto
    text = build_text_from_row(row)
    print(f"\nTexto (primeras 300 chars):")
    print(f"  {text[:300]}...")
    
    # Preparar payload
    item = {
        "id": str(row["id"]),
        "text": text
    }
    
    try:
        # Llamar al endpoint
        print(f"\nEnviando solicitud al servidor...")
        response = requests.post(
            SENTIMENT_ENDPOINT, 
            json={"items": [item]}, 
            timeout=120
        )
        response.raise_for_status()
        
        result_data = response.json()
        results = result_data.get("results", [])
        
        if not results:
            print("El servidor no devolvió resultados.")
            return
        
        # Mostrar resultado
        result = results[0]
        print(f"\nResultado del Análisis:")
        print(f"  - Sentimiento: {result.get('sentiment', 'N/A').upper()}")
        print(f"  - Confianza: {result.get('score', 0):.2f}")
        print(f"  - Explicación: {result.get('explanation', 'N/A')}")
        
    except requests.exceptions.Timeout:
        print("Error: Timeout esperando respuesta del servidor")
    except requests.exceptions.ConnectionError:
        print("Error: No se pudo conectar al servidor. ¿Está corriendo?")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Función principal de prueba."""

    if not Path(PARQUET_PATH).exists():
        print(f"Dataset no encontrado en {PARQUET_PATH}. Se omiten las pruebas interactivas de sentimiento.")
        return

    print("Cargando dataset...")
    df = pd.read_parquet(PARQUET_PATH, engine="fastparquet")
    print(f"Dataset cargado: {len(df)} registros")
    
    # Prueba 1: Primer registro
    print(f"\n{'#'*80}")
    print("PRUEBA 1: Análisis del primer registro")
    print(f"{'#'*80}")
    analyze_single_message(df, df.iloc[0]["id"])
    
    # Prueba 2: Registro en posición 10
    if len(df) > 10:
        print(f"\n{'#'*80}")
        print("PRUEBA 2: Análisis del registro en posición 10")
        print(f"{'#'*80}")
        analyze_single_message(df, df.iloc[10]["id"])
    
    # Prueba 3: Registro en posición 25
    if len(df) > 25:
        print(f"\n{'#'*80}")
        print("PRUEBA 3: Análisis del registro en posición 25")
        print(f"{'#'*80}")
        analyze_single_message(df, df.iloc[25]["id"])
    
    # Prueba 4: Registro en posición 50
    if len(df) > 50:
        print(f"\n{'#'*80}")
        print("PRUEBA 4: Análisis del registro en posición 50")
        print(f"{'#'*80}")
        analyze_single_message(df, df.iloc[50]["id"])
    
    print(f"\n{'='*80}")
    print("FIN DE LAS PRUEBAS")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
