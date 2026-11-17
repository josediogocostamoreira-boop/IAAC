import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os

if __package__:
    from .project_paths import DEFAULT_DATASET_PATH, PROJECT_ROOT, validate_dataset_path
else:
    from project_paths import DEFAULT_DATASET_PATH, PROJECT_ROOT, validate_dataset_path


def summarize(df, out_dir='outputs'):
    os.makedirs(out_dir, exist_ok=True)
    df.head(10).to_csv(os.path.join(out_dir, 'head.csv'), index=False)
    with open(os.path.join(out_dir, 'summary.txt'), 'w', encoding='utf-8') as f:
        f.write('Shape: ' + str(df.shape) + '\n\n')
        f.write('Dtypes:\n')
        f.write(str(df.dtypes) + '\n\n')
        f.write('Missing values:\n')
        f.write(str(df.isna().sum()) + '\n\n')
        f.write('Description (numeric):\n')
        numeric_columns = df.select_dtypes(include=[np.number])
        if numeric_columns.empty:
            f.write('No numeric columns.\n\n')
        else:
            f.write(str(numeric_columns.describe()) + '\n\n')
    # target distribution if label exists
    target_col = next((name for name in ('label', 'Label') if name in df.columns), None)
    if target_col:
        dist = df[target_col].value_counts()
        dist.to_csv(os.path.join(out_dir, 'label_distribution.csv'))
        plt.figure(figsize=(8,4))
        sns.countplot(data=df, x=target_col)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'label_distribution.png'))
        plt.close()


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATASET_PATH
    df = pd.read_csv(validate_dataset_path(path))
    print('Loaded', df.shape, 'rows')
    out_dir = sys.argv[2] if len(sys.argv) > 2 else PROJECT_ROOT / 'outputs'
    summarize(df, out_dir=out_dir)
    print(f'EDA outputs saved to {out_dir}')
