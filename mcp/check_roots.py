import pandas as pd
import numpy as np

PARQUET_PATH = "../data/reto.parquet"


def to_bool(series: pd.Series) -> pd.Series:
    """Convierte columnas object/str a bool de forma robusta."""
    return series.astype(str).str.strip().str.lower().isin(["true", "1", "t", "yes", "y"])


def load_dataset(path: str = PARQUET_PATH) -> pd.DataFrame:
    df = pd.read_parquet(path)

    # Normalizar columnas booleanas que vamos a usar
    for col in ["isComment", "isRetweet", "isDeleted", "isAdvertisement", "isBot"]:
        if col in df.columns:
            df[col + "_bool"] = to_bool(df[col])
        else:
            # Si no existe, asumimos False
            df[col + "_bool"] = False

    # Limpiar parentId: marcar como NaN los "no padre"
    no_parent_tokens = ["", "null", "none", "nan", "na", "nil", "0"]
    df["parentId_clean"] = (
        df["parentId"]
        .astype(str)
        .str.strip()
        .replace(no_parent_tokens, np.nan)
    )

    return df


def roots_method_1(df: pd.DataFrame) -> pd.DataFrame:
    """
    Método 1 (heurístico):
    - No es comentario
    - No es retweet
    - No está borrado / no es anuncio / no es bot
    - No tiene parentId (limpio)
    """
    roots = df[
        (~df["isComment_bool"]) &
        (~df["isRetweet_bool"]) &
        (~df["isDeleted_bool"]) &
        (~df["isAdvertisement_bool"]) &
        (~df["isBot_bool"]) &
        (df["parentId_clean"].isna())
    ].copy()
    return roots


def roots_method_2(df: pd.DataFrame) -> pd.DataFrame:
    """
    Método 2 (nuevo):
    - Root se define porque id == threadId
    Opcionalmente podrías filtrar lo mismo que en el método 1,
    pero aquí lo dejamos solo con esa regla para ver la diferencia.
    """
    roots = df[df["id"] == df["threadId"]].copy()
    return roots


def compare_roots():
    df = load_dataset()

    r1 = roots_method_1(df)
    r2 = roots_method_2(df)

    ids_r1 = set(r1["id"])
    ids_r2 = set(r2["id"])

    common_ids = ids_r1 & ids_r2
    only_r1 = ids_r1 - ids_r2
    only_r2 = ids_r2 - ids_r1

    print("========== RESUMEN ==========")
    print(f"Total filas en dataset: {len(df)}")
    print(f"Roots Método 1 (heurístico): {len(r1)}")
    print(f"Roots Método 2 (id == threadId): {len(r2)}")
    print(f"Roots en común (M1 ∩ M2): {len(common_ids)}")
    print(f"Solo en Método 1 (M1 - M2): {len(only_r1)}")
    print(f"Solo en Método 2 (M2 - M1): {len(only_r2)}")

    # Algunos ejemplos
    print("\n=== Ejemplos comunes (M1 ∩ M2) ===")
    if common_ids:
        common_sample = r1[r1["id"].isin(list(common_ids))].head(5)
        print(common_sample[["id", "threadId", "parentId", "isComment", "isRetweet"]])
    else:
        print("No hay roots comunes.")

    print("\n=== Ejemplos solo Método 1 (M1 - M2) ===")
    if only_r1:
        only_r1_sample = r1[r1["id"].isin(list(only_r1))].head(5)
        print(only_r1_sample[["id", "threadId", "parentId", "isComment", "isRetweet"]])
    else:
        print("No hay roots exclusivos de M1.")

    print("\n=== Ejemplos solo Método 2 (M2 - M1) ===")
    if only_r2:
        only_r2_sample = r2[r2["id"].isin(list(only_r2))].head(5)
        print(only_r2_sample[["id", "threadId", "parentId", "isComment", "isRetweet"]])
    else:
        print("No hay roots exclusivos de M2.")


if __name__ == "__main__":
    compare_roots()
