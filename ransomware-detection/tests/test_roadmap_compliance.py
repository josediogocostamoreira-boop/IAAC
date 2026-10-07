from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.data_preprocessing import Log1pSkewedNonNegative
from src.roadmap_eda import generate_eda
from src.supervised_learning import train_and_compare


def make_dataset(rows_per_class: int = 30) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    records = []
    for label, shift in (("Benign", 0.0), ("Malware", 3.0)):
        for index in range(rows_per_class):
            records.append(
                {
                    "md5": f"{label}-{index}",
                    "sha1": f"sha-{label}-{index}",
                    "Class": label,
                    "Category": "Benign" if label == "Benign" else "Ransomware",
                    "Family": "Benign" if label == "Benign" else "TestFamily",
                    "size": float(rng.lognormal(mean=shift, sigma=0.6)),
                    "signed_value": float(rng.normal(loc=shift, scale=1.0)),
                    "machine": "x86" if label == "Benign" else "x64",
                }
            )
    return pd.DataFrame(records)


class FeatureEngineeringTests(unittest.TestCase):
    def test_log_transform_is_fit_on_training_values_and_preserves_other_columns(self):
        train = np.array([[0.0, -10.0], [1.0, -2.0], [5.0, -3.0], [100.0, -4.0]])
        transformer = Log1pSkewedNonNegative().fit(train)
        transformed = transformer.transform(np.array([[10.0, -7.0]]))

        self.assertTrue(transformer.log_mask_[0])
        self.assertFalse(transformer.log_mask_[1])
        self.assertAlmostEqual(transformed[0, 0], np.log1p(10.0))
        self.assertEqual(transformed[0, 1], -7.0)


class RoadmapEdaTests(unittest.TestCase):
    def test_eda_creates_univariate_bivariate_correlation_and_pca_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "dataset.csv"
            output_dir = root / "eda"
            make_dataset().to_csv(data_path, index=False)

            summary = generate_eda(data_path, output_dir)

            self.assertEqual(summary["rows_after_cleaning"], 60)
            self.assertEqual(summary["class_distributions"]["Class"]["Benign"], 30)
            self.assertEqual(summary["correlations"]["numeric_features"], 2)
            for artifact in (
                "numeric_univariate_summary.csv",
                "categorical_univariate_summary.csv",
                "numeric_vs_class_tests.csv",
                "categorical_vs_class_tests.csv",
                "pearson_correlation.csv",
                "spearman_correlation.csv",
                "pearson_heatmap.png",
                "spearman_heatmap.png",
                "pca_scores.csv",
                "pca_class_scatter.png",
                "eda_summary.json",
            ):
                self.assertTrue((output_dir / artifact).is_file(), artifact)


class SupervisedOptimizationTests(unittest.TestCase):
    def test_model_selection_runs_cv_tuning_and_reports_fit_diagnostic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_path = root / "dataset.csv"
            output_dir = root / "results"
            model_dir = root / "models"
            make_dataset(rows_per_class=20).to_csv(data_path, index=False)

            results = train_and_compare(
                data_path,
                output_dir,
                model_dir=model_dir,
                dataset_name="synthetic-test",
                cv_folds=2,
            )
            report = json.loads(
                (output_dir / "supervised_learning_report.json").read_text(
                    encoding="utf-8"
                )
            )

            self.assertFalse(results.empty)
            self.assertEqual(report["cross_validation"]["folds"], 2)
            self.assertFalse(report["model_selection"]["test_used_for_selection"])
            self.assertIn("best_parameters", report["cross_validation"])
            self.assertIn(
                report["cross_validation"]["fit_diagnostic"],
                {
                    "potential_overfitting",
                    "potential_underfitting",
                    "no_strong_recall_signal_of_underfit_or_overfit",
                },
            )
            self.assertTrue((output_dir / "hyperparameter_search.csv").is_file())
            self.assertTrue((output_dir / "supervised_confusion_matrix.png").is_file())
            self.assertTrue(
                (model_dir / f"{report['selected_model']}.joblib").is_file()
            )


if __name__ == "__main__":
    unittest.main()
