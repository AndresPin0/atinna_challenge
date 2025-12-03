from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
import re

from ..models.propagation_models import PropagationMessage


def _parse_dt(dt_str: str) -> datetime:
    # Intenta parsear ISO 8601; ajústalo si tu formato es distinto
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _tokenize(text: str) -> List[str]:
    text = text.lower()
    tokens = re.findall(r"\w+", text)
    return tokens


def _content_overlap(root_text: str, reply_text: str) -> float:
    if not root_text or not reply_text:
        return 0.0
    root_tokens = set(_tokenize(root_text))
    reply_tokens = set(_tokenize(reply_text))
    if not root_tokens or not reply_tokens:
        return 0.0
    inter = len(root_tokens & reply_tokens)
    union = len(root_tokens | reply_tokens)
    return inter / union if union > 0 else 0.0


def compute_propagation(
    root_id: str,
    messages: List[PropagationMessage],
) -> Dict[str, Any]:
    # Índice por id
    by_id: Dict[str, PropagationMessage] = {m.id: m for m in messages}
    if root_id not in by_id:
        raise ValueError(f"root_id {root_id} no se encuentra en messages")

    root = by_id[root_id]
    root_time = _parse_dt(root.createdAt)
    root_text = root.text or ""

    # Construimos hijos por parentId
    children_by_parent: Dict[str, List[PropagationMessage]] = defaultdict(list)
    for m in messages:
        if m.parentId:
            children_by_parent[m.parentId].append(m)

    # BFS para obtener descendientes, niveles, tiempos, etc.
    queue: List[Tuple[PropagationMessage, int]] = []  # (msg, depth)
    descendants: List[Tuple[PropagationMessage, int]] = []

    for child in children_by_parent.get(root_id, []):
        queue.append((child, 1))

    while queue:
        current, depth = queue.pop(0)
        descendants.append((current, depth))
        for child in children_by_parent.get(current.id, []):
            queue.append((child, depth + 1))

    total_replies = len(descendants)
    direct_replies = len(children_by_parent.get(root_id, []))
    indirect_replies = total_replies - direct_replies

    if total_replies > 0:
        max_depth = max(depth for _, depth in descendants)
    else:
        max_depth = 0

    # Autores
    authors = set()
    if root.authorId:
        authors.add(root.authorId)
    for msg, _ in descendants:
        if msg.authorId:
            authors.add(msg.authorId)
    unique_authors = len(authors)

    # Velocidad: tiempos
    reply_times = [_parse_dt(msg.createdAt) for msg, _ in descendants]
    reply_times.sort()

    if reply_times:
        time_to_first = (reply_times[0] - root_time).total_seconds() / 60.0
        # 50% de las replies
        half_idx = max(0, int(len(reply_times) * 0.5) - 1)
        time_to_half = (reply_times[half_idx] - root_time).total_seconds() / 60.0
    else:
        time_to_first = 0.0
        time_to_half = 0.0

    # Niveles
    level_counter = Counter()
    for _, depth in descendants:
        level_counter[depth] += 1
    levels = [
        {"depth": depth, "count": count}
        for depth, count in sorted(level_counter.items())
    ]

    # Time series (buckets por hora desde root_time)
    bucket_counter = Counter()
    for t in reply_times:
        # bucket = hora relativa al root_time (ej: 10:00, 11:00, etc.)
        delta = t - root_time
        hours = int(delta.total_seconds() // 3600)
        bucket_start = root_time + timedelta(hours=hours)
        bucket_counter[bucket_start] += 1

    time_series = [
        {"bucket_start": b.isoformat(), "count": c}
        for b, c in sorted(bucket_counter.items())
    ]

    # Overlap de contenido
    overlaps: List[Tuple[PropagationMessage, int, float]] = []
    for msg, depth in descendants:
        score = _content_overlap(root_text, msg.text or "")
        overlaps.append((msg, depth, score))

    if overlaps:
        avg_content_overlap = sum(s for _, _, s in overlaps) / len(overlaps)
    else:
        avg_content_overlap = 0.0

    # Top replies por engagementRate / influenceScore
    def engagement_key(x: Tuple[PropagationMessage, int, float]) -> float:
        msg, _, _ = x
        er = msg.engagementRate or 0.0
        inf = msg.influenceScore or 0.0
        return er + inf

    top_overlaps = sorted(overlaps, key=engagement_key, reverse=True)[:5]
    top_engaged_replies = [
        {
            "id": msg.id,
            "authorId": msg.authorId,
            "createdAt": msg.createdAt,
            "engagementRate": msg.engagementRate or 0.0,
            "influenceScore": msg.influenceScore or 0.0,
            "depth": depth,
            "content_overlap": score,
        }
        for msg, depth, score in top_overlaps
    ]

    # Propagation score (simplificado y tunable)
    # Normalizaciones muy básicas para tener algo explicable:
    # - replies_norm: saturamos en 100 replies
    # - depth_norm: saturamos en depth=5
    # - authors_norm: saturamos en 50 autores
    replies_norm = min(total_replies, 100) / 100.0
    depth_norm = min(max_depth, 5) / 5.0
    authors_norm = min(unique_authors, 50) / 50.0
    overlap_norm = avg_content_overlap  # ya está en 0–1

    propagation_score = (
        0.35 * replies_norm
        + 0.2 * depth_norm
        + 0.25 * authors_norm
        + 0.2 * overlap_norm
    )

    return {
        "root_id": root_id,
        "summary": {
            "total_replies": total_replies,
            "direct_replies": direct_replies,
            "indirect_replies": indirect_replies,
            "unique_authors": unique_authors,
            "max_depth": max_depth,
            "time_to_first_reply_minutes": round(time_to_first, 2),
            "time_to_50pct_replies_minutes": round(time_to_half, 2),
            "avg_content_overlap": round(avg_content_overlap, 3),
            "propagation_score": round(propagation_score, 3),
        },
        "levels": levels,
        "time_series": time_series,
        "top_engaged_replies": top_engaged_replies,
    }
