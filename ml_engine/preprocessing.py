"""
NeuroScreen AI - Leak-Free Clinical Preprocessing Pipeline
Fits imputers, standardizers, and encoders strictly on training data within folds.
Prevents data leakage across validation and independent holdout test sets.
"""

from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder


class ClinicalDataPreprocessor(BaseEstimator, TransformerMixin):
    """
    Modular clinical data preprocessor with strict fold isolation.
    - Numerical: Median imputation + optional StandardScaler
    - Categorical: Constant 'missing' imputation + OneHotEncoder(handle_unknown='ignore')
    - Binary: Passthrough / boolean cast with 0 imputation
    """

    def __init__(
        self,
        numerical_cols: List[str] = None,
        categorical_cols: List[str] = None,
        binary_cols: List[str] = None,
        scale_numerical: bool = True
    ):
        self.numerical_cols = numerical_cols or ['Age_Mons']
        self.categorical_cols = categorical_cols or [
            'Sex', 'Ethnicity', 'Jaundice', 'Family_mem_with_ASD', 'Who completed the test'
        ]
        self.binary_cols = binary_cols or [f'A{i}' for i in range(1, 11)]
        self.scale_numerical = scale_numerical
        self.pipeline: Optional[ColumnTransformer] = None
        self.feature_names_out_: List[str] = []
        self._is_fitted = False

    def _build_column_transformer(self, X: pd.DataFrame) -> ColumnTransformer:
        available = set(X.columns)
        actual_num = [c for c in self.numerical_cols if c in available]
        actual_cat = [c for c in self.categorical_cols if c in available]
        actual_bin = [c for c in self.binary_cols if c in available]

        self.actual_num_ = actual_num
        self.actual_cat_ = actual_cat
        self.actual_bin_ = actual_bin

        transformers = []

        # 1. Numerical pipeline
        if actual_num:
            num_steps = [('imputer', SimpleImputer(strategy='median'))]
            if self.scale_numerical:
                num_steps.append(('scaler', StandardScaler()))
            num_pipeline = Pipeline(steps=num_steps)
            transformers.append(('num', num_pipeline, actual_num))

        # 2. Categorical pipeline
        if actual_cat:
            cat_pipeline = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
                ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
            ])
            transformers.append(('cat', cat_pipeline, actual_cat))

        # 3. Binary pipeline
        if actual_bin:
            bin_pipeline = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='constant', fill_value=0))
            ])
            transformers.append(('bin', bin_pipeline, actual_bin))

        return ColumnTransformer(
            transformers=transformers,
            remainder='drop'
        )

    def fit(self, X: pd.DataFrame, y=None):
        self.pipeline = self._build_column_transformer(X)
        self.pipeline.fit(X, y)
        self._is_fitted = True

        # Extract generated feature names
        try:
            names = []
            if self.actual_num_:
                names.extend(self.actual_num_)
            if self.actual_cat_:
                cat_encoder = self.pipeline.named_transformers_['cat'].named_steps['encoder']
                cat_feature_names = cat_encoder.get_feature_names_out(self.actual_cat_)
                names.extend(list(cat_feature_names))
            if self.actual_bin_:
                names.extend(self.actual_bin_)
            self.feature_names_out_ = names
        except Exception:
            self.feature_names_out_ = [f"f_{i}" for i in range(self.transform(X.iloc[:2]).shape[1])]

        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        if not self._is_fitted or self.pipeline is None:
            raise RuntimeError("ClinicalDataPreprocessor must be fitted before transform.")
        return self.pipeline.transform(X)

    def fit_transform(self, X: pd.DataFrame, y=None) -> np.ndarray:
        return self.fit(X, y).transform(X)

    def get_feature_names_out(self) -> List[str]:
        return list(self.feature_names_out_)

