import pandas as pd
import requests
import sys
from datetime import datetime, timezone
from pathlib import Path

PARQUET_PATH = "data/Reto_data.parquet"
PROPAGATION_ENDPOINT = "http://localhost:8000/api/v1/analysis/propagation"


# ==========================
# HELPERS
# ==========================

def epoch_ms_to_iso(value) -> str:
    try:
        ms = int(value)
    except (ValueError, TypeError):
        return str(value)
    dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return dt.isoformat()


def parse_bool(val) -> bool:
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in ("true", "1", "t", "yes", "y")


def safe_float(val, default: float = 0.0) -> float:
    try:
        if val is None:
            return default
        s = str(val).strip()
        if s == "" or s.lower() in ("nan", "none", "null"):
            return default
        return float(s)
    except (ValueError, TypeError):
        return default


def load_dataset(path: str = PARQUET_PATH) -> pd.DataFrame:
    return pd.read_parquet(path)


def is_valid_root(df: pd.DataFrame, message_id: str) -> tuple[bool, str]:
    """
    Verifica si un mensaje es un root válido.
    Retorna (es_válido, razón)
    """
    row = df[df["id"] == message_id]
    if row.empty:
        return False, f"El ID '{message_id}' no existe en el dataset"
    
    row = row.iloc[0]
    
    # Normalizar parentId
    no_parent_tokens = ["", "null", "none", "nan", "na", "nil", "0"]
    parent_str = str(row["parentId"]).strip().lower()
    has_parent = parent_str not in no_parent_tokens and pd.notna(row["parentId"])
    
    if has_parent:
        return False, f"Este mensaje tiene un parent (parentId={row['parentId']}), no es root"
    
    # Verificar si es el threadId
    thread_id = row["threadId"]
    if str(message_id) == str(thread_id):
        return True, "Es el root oficial (id == threadId)"
    
    # Verificar si hay otros mensajes sin parent en este thread
    df_thread = df[df["threadId"] == thread_id].copy()
    df_thread["parentId_str"] = df_thread["parentId"].astype(str).str.strip().str.lower()
    other_roots = df_thread[df_thread["parentId_str"].isin(no_parent_tokens) & (df_thread["id"] != message_id)]
    
    if len(other_roots) > 0:
        return True, f"Es un root válido pero hay {len(other_roots)} mensaje(s) más sin parent en este thread"
    
    return True, "Es el único mensaje sin parent en este thread"


def show_root_impact(df: pd.DataFrame, root_id: str, propagation_data: dict):
    """
    Muestra información detallada sobre el impacto del root message.
    """
    root_row = df[df["id"] == root_id].iloc[0]
    summary = propagation_data["summary"]
    
    print("\n" + "="*80)
    print("ANÁLISIS DE IMPACTO DEL ROOT MESSAGE")
    print("="*80)
    
    print(f"\nROOT MESSAGE:")
    print(f"  ID: {root_id}")
    print(f"  Author: {root_row.get('author', 'N/A')}")
    print(f"  Created: {datetime.fromtimestamp(int(root_row['createdAt'])/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Text preview: {str(root_row.get('text', 'N/A'))[:100]}...")
    print(f"  Engagement Rate: {safe_float(root_row.get('engagementRate')):.4f}")
    print(f"  Influence Score: {safe_float(root_row.get('influenceScore')):.4f}")
    
    print(f"\nMAGNITUD DEL IMPACTO:")
    print(f"  Total de respuestas generadas: {summary.get('total_replies', 0)}")
    print(f"  Profundidad máxima alcanzada: {summary.get('max_depth', 0)} niveles")
    print(f"  Autores únicos que participaron: {summary.get('unique_authors', 0)}")
    if 'time_to_first_reply' in summary:
        print(f"  Tiempo hasta primera respuesta: {summary['time_to_first_reply']}")
    print(f"  Promedio de similitud de contenido: {summary.get('avg_content_overlap', 0):.2%}")
    print(f"  Score de propagación: {summary.get('propagation_score', 0):.2f}/100")
    
    # Calcular métricas adicionales de impacto
    thread_id = root_row["threadId"]
    df_thread = df[df["threadId"] == thread_id]
    
    # Alcance por nivel
    levels = propagation_data.get("levels", [])
    if levels:
        print(f"\nDISTRIBUCIÓN DE RESPUESTAS POR NIVEL:")
        for lvl in levels:
            if lvl['depth'] == 0:
                continue
            percentage = (lvl['count'] / summary['total_replies'] * 100) if summary['total_replies'] > 0 else 0
            print(f"  Nivel {lvl['depth']}: {lvl['count']} mensajes ({percentage:.1f}%)")
    
    # Engagement acumulado del thread
    total_engagement = df_thread['engagementRate'].apply(safe_float).sum()
    avg_engagement = total_engagement / len(df_thread) if len(df_thread) > 0 else 0
    print(f"\nENGAGEMENT DEL THREAD:")
    print(f"  Engagement total acumulado: {total_engagement:.4f}")
    print(f"  Engagement promedio por mensaje: {avg_engagement:.4f}")
    print(f"  Engagement del root: {safe_float(root_row.get('engagementRate')):.4f}")
    
    # Factor de viralidad (cuántas veces se amplificó)
    if safe_float(root_row.get('engagementRate')) > 0:
        amplification = avg_engagement / safe_float(root_row.get('engagementRate'))
        print(f"  Factor de amplificación: {amplification:.2f}x")
    
    # Análisis de impacto del contenido del root
    print(f"\nIMPACTO DEL CONTENIDO DEL ROOT:")
    print(f"  Similitud promedio con replies: {summary.get('avg_content_overlap', 0):.2%}")
    
    # Calcular distribución de overlap
    top_replies = propagation_data.get("top_engaged_replies", [])
    if top_replies:
        overlaps = [r.get('content_overlap', 0) for r in top_replies]
        if overlaps:
            max_overlap = max(overlaps)
            min_overlap = min(overlaps)
            print(f"  Overlap máximo (top replies): {max_overlap:.2%}")
            print(f"  Overlap mínimo (top replies): {min_overlap:.2%}")
    
    # Engagement e Influence del root
    print(f"\nMÉTRICAS DEL ROOT:")
    print(f"  Engagement Rate: {safe_float(root_row.get('engagementRate')):.4f}")
    print(f"  Influence Score: {safe_float(root_row.get('influenceScore')):.4f}")
    
    # Comparar con métricas promedio de replies
    if top_replies:
        avg_reply_engagement = sum(r.get('engagementRate', 0) for r in top_replies) / len(top_replies)
        avg_reply_influence = sum(r.get('influenceScore', 0) for r in top_replies) / len(top_replies)
        print(f"\nCOMPARACIÓN ROOT vs REPLIES (top 5):")
        print(f"  Engagement - Root: {safe_float(root_row.get('engagementRate')):.4f} | Avg Replies: {avg_reply_engagement:.4f}")
        print(f"  Influence - Root: {safe_float(root_row.get('influenceScore')):.4f} | Avg Replies: {avg_reply_influence:.4f}")
    
    print("\n" + "="*80)


def choose_root_in_thread(df_thread: pd.DataFrame) -> str:
    """
    Lógica combinada de root dentro de un thread:
    1) Si hay id == threadId y parentId vacío -> root.
    2) Si no, tomamos el mensaje más antiguo sin parent, no comment, no retweet.
    """
    thread_id = df_thread["threadId"].iloc[0]

    # normalizar parentId "vacío"
    no_parent_tokens = ["", "null", "none", "nan", "na", "nil", "0"]
    parent_clean = (
        df_thread["parentId"]
        .astype(str)
        .str.strip()
        .replace(no_parent_tokens, pd.NA)
    )

    df_thread = df_thread.copy()
    df_thread["parentId_clean"] = parent_clean
    df_thread["isComment_bool"] = df_thread["isComment"].astype(str).str.lower().isin(["true", "1", "t", "yes", "y"])
    df_thread["isRetweet_bool"] = df_thread["isRetweet"].astype(str).str.lower().isin(["true", "1", "t", "yes", "y"])
    df_thread["createdAt_dt"] = pd.to_datetime(df_thread["createdAt"].astype("int64"), unit="ms", utc=True, errors="coerce")

    # 1) preferimos id == threadId
    m2 = df_thread[(df_thread["id"] == thread_id) & (df_thread["parentId_clean"].isna())]
    if not m2.empty:
        return str(m2.sort_values("createdAt_dt").iloc[0]["id"])

    # 2) fallback: mensaje más viejo sin parent, no comment, no retweet
    candidates = df_thread[
        (~df_thread["isComment_bool"]) &
        (~df_thread["isRetweet_bool"]) &
        (df_thread["parentId_clean"].isna())
    ].sort_values("createdAt_dt")

    if not candidates.empty:
        return str(candidates.iloc[0]["id"])

    # 3) último fallback: el más viejo del thread
    return str(df_thread.sort_values("createdAt_dt").iloc[0]["id"])


def build_mcp_messages(df_conv: pd.DataFrame) -> list:
    msgs = []
    for _, r in df_conv.iterrows():
        author_id = str(r.get("authorId")) if pd.notna(r.get("authorId")) and r.get("authorId") != "" else None
        msgs.append({
            "id": str(r["id"]),
            "parentId": str(r["parentId"]) if pd.notna(r.get("parentId")) and str(r["parentId"]).strip() != "" else None,
            "threadId": str(r.get("threadId")) if r.get("threadId") is not None else None,
            "authorId": author_id,
            "createdAt": epoch_ms_to_iso(r["createdAt"]),
            "text": r.get("text") if pd.notna(r.get("text")) else None,
            "isComment": parse_bool(r.get("isComment")) if "isComment" in r else None,
            "isRetweet": parse_bool(r.get("isRetweet")) if "isRetweet" in r else None,
            "engagementRate": safe_float(r.get("engagementRate")),
            "influenceScore": safe_float(r.get("influenceScore")),
        })
    return msgs


def demo_propagation_from_message_id(message_id: str, df: pd.DataFrame = None):
    if df is None:
        df = load_dataset()

    # 1) Verificar si el mensaje es un root válido
    is_root, reason = is_valid_root(df, message_id)
    
    print(f"\n{'='*80}")
    print(f"VERIFICACIÓN DE ROOT ID")
    print(f"{'='*80}")
    print(f"Message ID: {message_id}")
    print(f"¿Es root válido?: {'SÍ' if is_root else 'NO'}")
    print(f"Razón: {reason}")
    
    if not is_root:
        print(f"\nADVERTENCIA: Este mensaje no es un root válido.")
        response = input("¿Deseas continuar de todos modos? (s/n): ").strip().lower()
        if response not in ['s', 'si', 'sí', 'y', 'yes']:
            print("Operación cancelada.")
            return
        print("\nContinuando con el análisis...\n")
    
    # 2) info del mensaje consultado
    row = df[df["id"] == message_id]
    if row.empty:
        raise ValueError(f"No existe mensaje con id={message_id}")
    row = row.iloc[0]
    thread_id = row["threadId"]

    print(f"\n[DEBUG] Message ID consultado: {message_id}")
    print(f"[DEBUG] Thread ID: {thread_id}")
    print(f"[DEBUG] Parent ID del mensaje: '{row['parentId']}'")

    # 3) subset del thread
    df_thread = df[df["threadId"] == thread_id].copy()
    print(f"[DEBUG] Mensajes totales en este thread: {len(df_thread)}")

    # 4) usar el mensaje proporcionado como root
    root_id = message_id
    print(f"[DEBUG] Root ID usado: {root_id}")

    direct_children = df_thread[df_thread["parentId"] == root_id]
    print(f"[DEBUG] Hijos directos del root: {len(direct_children)}")

    # 5) payload al MCP
    messages = build_mcp_messages(df_thread)
    payload = {
        "root_id": root_id,
        "messages": messages,
    }

    # Debug: verificar que authorId se está enviando
    authors_sent = [m.get('authorId') for m in messages if m.get('authorId')]
    print(f"\n[DEBUG] Enviando {len(messages)} mensajes al MCP con root_id={root_id}")
    print(f"[DEBUG] AuthorIds únicos en payload: {len(set(authors_sent))}")
    print(f"[DEBUG] Ejemplos de authorId: {list(set(authors_sent))[:3]}")
    
    resp = requests.post(PROPAGATION_ENDPOINT, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # 6) Mostrar análisis de impacto detallado
    show_root_impact(df, root_id, data)

    print("\n[Resumen de propagación]")
    print("="*80)
    for k, v in data["summary"].items():
        print(f"  {k}: {v}")

    print("\n[Niveles de conversación]")
    for lvl in data["levels"]:
        print(f"  Profundidad {lvl['depth']}: {lvl['count']} mensajes")

    print("\n[Top replies por impacto]")
    print("=" * 80)
    for i, t in enumerate(data["top_engaged_replies"], 1):
        print(f"\n  {i}. ID: {t['id']}")
        print(f"     Profundidad: {t['depth']}")
        print(f"     Engagement Rate: {t['engagementRate']:.4f}")
        print(f"     Influence Score: {t.get('influenceScore', 0):.4f}")
        print(f"     Content Overlap: {t.get('content_overlap', 0):.2%}")
        print(f"     Author ID: {t.get('authorId', 'N/A')}")


def interactive_mode(df: pd.DataFrame):
    """
    Modo interactivo para que el usuario elija el root tweet.
    """
    print("\n" + "="*80)
    print("MODO INTERACTIVO - ANÁLISIS DE PROPAGACIÓN")
    print("="*80)
    
    # Mostrar threads más activos
    thread_counts = df.groupby("threadId").size().sort_values(ascending=False).head(10)
    print("\nTop 10 threads más activos:")
    for i, (thread_id, count) in enumerate(thread_counts.items(), 1):
        print(f"  {i}. Thread {thread_id}: {count} mensajes")
    
    # Mostrar posibles roots
    no_parent_tokens = ["", "null", "none", "nan", "na", "nil", "0"]
    df_copy = df.copy()
    df_copy["parentId_str"] = df_copy["parentId"].astype(str).str.strip().str.lower()
    potential_roots = df_copy[df_copy["parentId_str"].isin(no_parent_tokens)]
    
    print(f"\nHay {len(potential_roots)} mensajes sin parent en el dataset (posibles roots)")
    print("\nAlgunos ejemplos de posibles roots:")
    for i, (_, row) in enumerate(potential_roots.head(5).iterrows(), 1):
        text_preview = str(row.get('text', 'N/A'))[:60]
        print(f"  {i}. ID: {row['id']}")
        print(f"     Thread: {row['threadId']}")
        print(f"     Text: {text_preview}...")
        print(f"     Created: {datetime.fromtimestamp(int(row['createdAt'])/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')}")
        print()
    
    # Solicitar ID del usuario
    print("="*80)
    message_id = input("\nIngresa el ID del mensaje que deseas analizar como root: ").strip()
    
    if not message_id:
        print("No se proporcionó ningún ID. Operación cancelada.")
        return
    
    # Ejecutar análisis
    demo_propagation_from_message_id(message_id, df)



if __name__ == "__main__":
    if not Path(PARQUET_PATH).exists():
        print(f"[INFO] Dataset no encontrado en {PARQUET_PATH}. Se omiten las pruebas interactivas de propagación.")
        sys.exit(0)

    df = load_dataset()
    print(f"[INFO] Dataset cargado: {len(df)} registros")

    # Verificar si se pasó un ID como argumento
    if len(sys.argv) > 1:
        # Modo directo: usar el ID proporcionado como argumento
        message_id = sys.argv[1]
        print(f"[INFO] Analizando mensaje ID: {message_id}\n")
        demo_propagation_from_message_id(message_id, df)
    else:
        # Modo interactivo: permitir al usuario elegir
        interactive_mode(df)

