"""Generate reproducible statistical and visual EDA evidence for the roadmap."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

if __package__:
    from .data_preprocessing import (
        TARGET,
        convert_numeric_like_columns,
        feature_columns,
        load_and_deduplicate,
    )
else:
    from data_preprocessing import (
        TARGET,
        convert_numeric_like_columns,
        feature_columns,
        load_and_deduplicate,
    )


def benjamini_hochberg(p_values: list[float]) -> list[float]:
    """Return Benjamini-Hochberg adjusted p-values in input order."""
    values = np.asarray(p_values, dtype=float)
    if values.size == 0:
        return []
    order = np.argsort(values)
    ranked = values[order]
    adjusted = ranked * len(ranked) / np.arange(1, len(ranked) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    restored = np.empty_like(adjusted)
    restored[order] = np.minimum(adjusted, 1.0)
    return restored.tolist()


def numeric_summary(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    records = []
    for column in columns:
        values = frame[column].dropna()
        records.append(
            {
                "feature": column,
                "count": int(values.size),
                "missing": int(frame[column].isna().sum()),
                "mean": float(values.mean()) if not values.empty else np.nan,
                "std": float(values.std()) if values.size > 1 else np.nan,
                "min": float(values.min()) if not values.empty else np.nan,
                "q1": float(values.quantile(0.25)) if not values.empty else np.nan,
                "median": float(values.median()) if not values.empty else np.nan,
                "q3": float(values.quantile(0.75)) if not values.empty else np.nan,
                "max": float(values.max()) if not values.empty else np.nan,
                "skewness": float(values.skew()) if values.size > 2 else np.nan,
                "kurtosis": float(values.kurtosis()) if values.size > 3 else np.nan,
            }
        )
    return pd.DataFrame(records)


def numeric_bivariate_tests(
    frame: pd.DataFrame, columns: list[str], target: str = TARGET
) -> pd.DataFrame:
    benign = frame.loc[frame[target] == "Benign"]
    malware = frame.loc[frame[target] == "Malware"]
    records = []
    for column in columns:
        left = benign[column].dropna().to_numpy(dtype=float)
        right = malware[column].dropna().to_numpy(dtype=float)
        if not left.size or not right.size:
            continue
        result = stats.mannwhitneyu(left, right, alternative="two-sided")
        pooled = np.concatenate((left, right))
        ranks = stats.rankdata(pooled)
        rank_biserial = 2 * (
            ranks[left.size :].sum() - right.size * (right.size + 1) / 2
        ) / (left.size * right.size) - 1
        records.append(
            {
                "feature": column,
                "benign_median": float(np.median(left)),
                "malware_median": float(np.median(right)),
                "mann_whitney_u": float(result.statistic),
                "p_value": float(result.pvalue),
                "rank_biserial_effect": float(rank_biserial),
                "n_benign": int(left.size),
                "n_malware": int(right.size),
            }
        )
    result_frame = pd.DataFrame(records)
    if not result_frame.empty:
        result_frame["p_adjusted_bh"] = benjamini_hochberg(
            result_frame["p_value"].tolist()
        )
        result_frame.sort_values("p_adjusted_bh", inplace=True)
    return result_frame


def categorical_bivariate_tests(
    frame: pd.DataFrame, columns: list[str], target: str = TARGET
) -> pd.DataFrame:
    records = []
    for column in columns:
        contingency = pd.crosstab(frame[column].fillna("<MISSING>"), frame[target])
        if contingency.shape[0] < 2 or contingency.shape[1] < 2:
            continue
        chi2, p_value, _, _ = stats.chi2_contingency(contingency)
        total = int(contingency.to_numpy().sum())
        denominator = min(contingency.shape[0] - 1, contingency.shape[1] - 1)
        cramers_v = float(np.sqrt(chi2 / (total * denominator))) if denominator else 0.0
        records.append(
            {
                "feature": column,
                "chi2": float(chi2),
                "degrees_of_freedom": int((contingency.shape[0] - 1) * (contingency.shape[1] - 1)),
                "p_value": float(p_value),
                "cramers_v": cramers_v,
                "categories": int(contingency.shape[0]),
            }
        )
    result_frame = pd.DataFrame(records)
    if not result_frame.empty:
        result_frame["p_adjusted_bh"] = benjamini_hochberg(
            result_frame["p_value"].tolist()
        )
        result_frame.sort_values("p_adjusted_bh", inplace=True)
    return result_frame


def _save_class_distributions(frame: pd.DataFrame, output_dir: Path) -> dict:
    summaries = {}
    for column in (TARGET, "Category", "Family"):
        if column not in frame.columns:
            continue
        counts = (
            frame[column].fillna("<MISSING>").value_counts(dropna=False)
            .rename_axis(column)
            .reset_index(name="count")
        )
        counts.to_csv(output_dir / f"{column.lower()}_distribution.csv", index=False)
        summaries[column] = {
            str(row[column]): int(row["count"])
            for _, row in counts.iterrows()
        }
        if column != TARGET:
            counts = counts.head(30)
        plt.figure(figsize=(10, max(4, min(12, 0.28 * len(counts)))))
        sns.barplot(data=counts, x="count", y=column, color="#4472C4")
        plt.title(f"Distribuição de {column}")
        plt.tight_layout()
        plt.savefig(output_dir / f"{column.lower()}_distribution.png", dpi=140)
        plt.close()
    return summaries


def _save_correlation_evidence(
    frame: pd.DataFrame, numeric_columns: list[str], output_dir: Path
) -> dict[str, int]:
    if not numeric_columns:
        return {"numeric_features": 0, "pearson_pairs": 0, "spearman_pairs": 0}
    numeric = frame[numeric_columns]
    pearson = numeric.corr(method="pearson")
    spearman = numeric.corr(method="spearman")
    pearson.to_csv(output_dir / "pearson_correlation.csv")
    spearman.to_csv(output_dir / "spearman_correlation.csv")

    all_pairs: list[dict[str, object]] = []
    for method, matrix in (("pearson", pearson), ("spearman", spearman)):
        upper = matrix.where(np.triu(np.ones(matrix.shape), k=1).astype(bool))
        pairs = upper.stack().rename("correlation").reset_index()
        pairs.columns = ["feature_1", "feature_2", "correlation"]
        pairs.insert(0, "method", method)
        all_pairs.extend(pairs.to_dict(orient="records"))
        high = pairs[pairs["correlation"].abs() >= 0.80].copy()
        high["abs_correlation"] = high["correlation"].abs()
        high.sort_values("abs_correlation", ascending=False, inplace=True)
        high.to_csv(output_dir / f"high_{method}_pairs.csv", index=False)

        variances = numeric.var().sort_values(ascending=False)
        selected = variances.head(25).index
        plt.figure(figsize=(12, 10))
        sns.heatmap(
            matrix.loc[selected, selected],
            cmap="vlag",
            center=0,
            vmin=-1,
            vmax=1,
            square=True,
            xticklabels=True,
            yticklabels=True,
        )
        plt.title(f"Matriz de correlação {method.title()} (25 features de maior variância)")
        plt.tight_layout()
        plt.savefig(output_dir / f"{method}_heatmap.png", dpi=140)
        plt.close()
    pd.DataFrame(all_pairs).to_csv(output_dir / "correlation_pairs.csv", index=False)
    return {
        "numeric_features": len(numeric_columns),
        "pearson_pairs": len(numeric_columns) * (len(numeric_columns) - 1) // 2,
        "spearman_pairs": len(numeric_columns) * (len(numeric_columns) - 1) // 2,
    }


def _save_multivariate_evidence(
    frame: pd.DataFrame, numeric_columns: list[str], output_dir: Path
) -> dict:
    if len(numeric_columns) < 2 or len(frame) < 2:
        return {"status": "not enough numeric data for PCA"}
    numeric = frame[numeric_columns].replace([np.inf, -np.inf], np.nan)
    prepared = SimpleImputer(strategy="median").fit_transform(numeric)
    scaled = StandardScaler().fit_transform(prepared)
    pca = PCA(n_components=2, random_state=42)
    coordinates = pca.fit_transform(scaled)
    scores = pd.DataFrame(
        {
            "PC1": coordinates[:, 0],
            "PC2": coordinates[:, 1],
            TARGET: frame[TARGET].to_numpy(),
        }
    )
    scores.to_csv(output_dir / "pca_scores.csv", index=False)
    loadings = pd.DataFrame(
        pca.components_.T,
        index=numeric_columns,
        columns=["PC1_loading", "PC2_loading"],
    )
    loadings.to_csv(output_dir / "pca_loadings.csv", index_label="feature")
    explained = {
        "PC1": float(pca.explained_variance_ratio_[0]),
        "PC2": float(pca.explained_variance_ratio_[1]),
        "cumulative_2_components": float(pca.explained_variance_ratio_.sum()),
        "scope": "descriptive EDA; fitted to the cleaned dataset, not a predictive model",
    }
    (output_dir / "pca_variance.json").write_text(
        json.dumps(explained, indent=2), encoding="utf-8"
    )
    plt.figure(figsize=(9, 6))
    sns.scatterplot(
        data=scores,
        x="PC1",
        y="PC2",
        hue=TARGET,
        alpha=0.45,
        s=18,
    )
    plt.title("PCA exploratória das features numéricas")
    plt.tight_layout()
    plt.savefig(output_dir / "pca_class_scatter.png", dpi=140)
    plt.close()
    return explained


def generate_eda(data_path: Path, output_dir: Path) -> dict:
    """Generate data summaries, inferential tests, correlations, and figures."""
    output_dir.mkdir(parents=True, exist_ok=True)
    frame, cleaning = load_and_deduplicate(data_path)
    frame = convert_numeric_like_columns(frame)
    columns = feature_columns(frame)
    numeric_columns = frame[columns].select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = [column for column in columns if column not in numeric_columns]

    distributions = _save_class_distributions(frame, output_dir)
    numeric_summary(frame, numeric_columns).to_csv(
        output_dir / "numeric_univariate_summary.csv", index=False
    )
    categorical_summary = pd.DataFrame(
        [
            {
                "feature": column,
                "unique_values": int(frame[column].nunique(dropna=True)),
                "missing": int(frame[column].isna().sum()),
                "mode": (
                    str(frame[column].mode(dropna=True).iloc[0])
                    if not frame[column].mode(dropna=True).empty
                    else ""
                ),
            }
            for column in categorical_columns
        ]
    )
    categorical_summary.to_csv(
        output_dir / "categorical_univariate_summary.csv", index=False
    )

    numeric_tests = numeric_bivariate_tests(frame, numeric_columns)
    categorical_tests = categorical_bivariate_tests(frame, categorical_columns)
    numeric_tests.to_csv(output_dir / "numeric_vs_class_tests.csv", index=False)
    categorical_tests.to_csv(
        output_dir / "categorical_vs_class_tests.csv", index=False
    )

    top_features = numeric_tests.head(6)["feature"].tolist()
    if top_features:
        fig, axes = plt.subplots(
            len(top_features), 1, figsize=(10, max(4, 2.7 * len(top_features)))
        )
        axes_list = np.atleast_1d(axes)
        for axis, column in zip(axes_list, top_features):
            sns.boxplot(data=frame, x=TARGET, y=column, ax=axis, showfliers=False)
            axis.set_title(f"{column}: Benign vs Malware")
        fig.tight_layout()
        fig.savefig(output_dir / "top_numeric_features_by_class.png", dpi=140)
        plt.close(fig)

    correlation_counts = _save_correlation_evidence(
        frame, numeric_columns, output_dir
    )
    pca_summary = _save_multivariate_evidence(frame, numeric_columns, output_dir)
    overview = {
        "source": str(data_path),
        "cleaning": cleaning,
        "rows_after_cleaning": len(frame),
        "feature_count": len(columns),
        "numeric_feature_count": len(numeric_columns),
        "categorical_feature_count": len(categorical_columns),
        "missing_values_total": int(frame[columns].isna().sum().sum()),
        "class_distributions": distributions,
        "correlations": correlation_counts,
        "numeric_class_tests": int(len(numeric_tests)),
        "categorical_class_tests": int(len(categorical_tests)),
        "multiple_testing_correction": "Benjamini-Hochberg FDR",
        "bivariate_numeric_test": "two-sided Mann-Whitney U; rank-biserial effect size",
        "bivariate_categorical_test": "chi-square; Cramer's V effect size",
        "pca": pca_summary,
        "interpretation_note": (
            "EDA associations are descriptive, not causal. Statistical p-values "
            "are adjusted for multiple comparisons. PCA is exploratory and uses "
            "all cleaned rows; it is not model validation."
        ),
    }
    (output_dir / "eda_summary.json").write_text(
        json.dumps(overview, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return overview


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate reproducible EDA evidence for the roadmap."
    )
    parser.add_argument("--data", type=Path, default=Path("ransom.csv"))
    parser.add_argument("--output", type=Path, default=Path("results/eda"))
    args = parser.parse_args()
    print(
        json.dumps(
            generate_eda(args.data, args.output), indent=2, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
