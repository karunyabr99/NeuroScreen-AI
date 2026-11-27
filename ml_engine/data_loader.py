"""
NeuroScreen AI - Dataset Loader and Schema Inspector
Supports arbitrary CSV uploads, automated schema inference, missing value analysis,
duplicate detection, and class balance analysis.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


class DatasetLoader:
    """
    Robust CSV dataset loader and schema inspector.
    """

    TARGET_CANDIDATES = [
        'class/asd traits', 'class/asd', 'class/asd traits ', 'asd', 'class',
        'target', 'diagnosis', 'label', 'outcome', 'asd_traits', 'group'
    ]

    ID_CANDIDATES = [
        'case_no', 'case_number', 'id', 'participant_id', 'subject_id', 'patient_id', 'child_id'
    ]

    LEAKAGE_CANDIDATES = [
        'qchat-10-score', 'qchat_10_score', 'score', 'total_score', 'aq-10-score', 'aq_score',
        'sum_qchat', 'result'
    ]

    @classmethod
    def load_csv(cls, file_path_or_buffer: Union[str, Path, Any]) -> pd.DataFrame:
        """
        Load CSV, ARFF, or SAV dataset and normalize column headers (trim leading/trailing whitespace).
        """
        if isinstance(file_path_or_buffer, (str, Path)):
            path = Path(file_path_or_buffer)
            if not path.exists():
                raise FileNotFoundError(f"Dataset file not found at: {path}")

            ext = path.suffix.lower()
            if ext == '.arff':
                from scipy.io import arff
                data, _ = arff.loadarff(path)
                df = pd.DataFrame(data)
                for col in df.select_dtypes([object]):
                    try:
                        df[col] = df[col].str.decode('utf-8')
                    except Exception:
                        pass
            elif ext == '.sav':
                import pyreadstat
                df, meta = pyreadstat.read_sav(path)
                # Map value labels for clearer inspection if available
                if meta and hasattr(meta, 'variable_value_labels'):
                    for var_name, labels in meta.variable_value_labels.items():
                        if var_name in df.columns:
                            df[var_name] = df[var_name].map(labels).fillna(df[var_name])
            else:
                df = pd.read_csv(path)
        else:
            df = pd.read_csv(file_path_or_buffer)

        # Clean column names (strip whitespace)
        df.columns = [str(c).strip() for c in df.columns]
        return df

    @classmethod
    def inspect_dataset(cls, df: pd.DataFrame, target_col: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive audit of dataset: schema, data types, missing values, duplicates,
        class distribution, and candidate column roles.
        """
        n_rows, n_cols = df.shape
        columns = list(df.columns)

        # 1. Target identification
        identified_target = target_col
        if not identified_target:
            for col in columns:
                if col.lower() in cls.TARGET_CANDIDATES:
                    identified_target = col
                    break

        # 2. Identifiers & Target leakage detection
        id_cols = [c for c in columns if c.lower() in cls.ID_CANDIDATES]
        leakage_cols = [c for c in columns if c.lower() in cls.LEAKAGE_CANDIDATES]

        # 3. Column type inference & Missing values
        column_details: List[Dict[str, Any]] = []
        missing_counts = df.isnull().sum()
        total_missing = int(missing_counts.sum())

        for col in columns:
            col_type = "numerical"
            unique_vals = df[col].dropna().unique()
            n_unique = len(unique_vals)

            if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
                if n_unique <= 2:
                    col_type = "binary"
                else:
                    col_type = "categorical"
            elif set(unique_vals).issubset({0, 1, 0.0, 1.0}):
                col_type = "binary"
            elif n_unique < 10 and not pd.api.types.is_float_dtype(df[col]):
                col_type = "categorical"
            else:
                col_type = "numerical"

            sample_vals = [str(v) for v in unique_vals[:5]]
            column_details.append({
                "name": col,
                "inferred_type": col_type,
                "missing_count": int(missing_counts[col]),
                "missing_percentage": round(float(missing_counts[col] / n_rows * 100), 2),
                "unique_values_count": int(n_unique),
                "sample_values": sample_vals,
                "is_target": col == identified_target,
                "is_id": col in id_cols,
                "is_potential_leakage": col in leakage_cols
            })

        # 4. Duplicate rows
        n_duplicates = int(df.duplicated().sum())

        # 5. Class balance analysis
        class_balance = {}
        if identified_target and identified_target in df.columns:
            target_series = df[identified_target].dropna().astype(str).str.strip().str.title()
            counts = target_series.value_counts().to_dict()
            total_valid = len(target_series)
            class_balance = {
                "counts": {k: int(v) for k, v in counts.items()},
                "ratios": {k: round(float(v / total_valid), 4) for k, v in counts.items()},
                "total_valid_target_rows": total_valid,
                "imbalance_ratio": round(float(max(counts.values()) / max(1, min(counts.values()))), 2) if len(counts) > 1 else 1.0
            }

        # 6. Preview rows (first 10 records as dict)
        preview_rows = df.head(10).replace({np.nan: None}).to_dict(orient="records")

        return {
            "row_count": n_rows,
            "column_count": n_cols,
            "identified_target": identified_target,
            "id_columns": id_cols,
            "leakage_columns": leakage_cols,
            "duplicate_rows_count": n_duplicates,
            "total_missing_cells": total_missing,
            "overall_missing_rate": round(float(total_missing / (n_rows * n_cols) * 100), 2) if n_rows * n_cols > 0 else 0.0,
            "columns": column_details,
            "class_balance": class_balance,
            "preview": preview_rows
        }

