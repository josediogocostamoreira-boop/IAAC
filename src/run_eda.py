import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os


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
        f.write(str(df.describe(include=[np.number])) + '\n\n')
    # target distribution if label exists
    if 'label' in df.columns:
        dist = df['label'].value_counts()
        dist.to_csv(os.path.join(out_dir, 'label_distribution.csv'))
        plt.figure(figsize=(8,4))
        sns.countplot(data=df, x='label')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, 'label_distribution.png'))
        plt.close()


if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '../archive/final_dataset.csv'
    df = pd.read_csv(path)
    print('Loaded', df.shape, 'rows')
    out_dir = sys.argv[2] if len(sys.argv) > 2 else 'outputs'
    summarize(df, out_dir=out_dir)
    print(f'EDA outputs saved to {out_dir}')
