from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_PATH = PROJECT_ROOT / 'archive' / 'final_dataset.csv'


def validate_dataset_path(path):
    dataset_path = Path(path).expanduser()
    if not dataset_path.is_absolute():
        dataset_path = (Path.cwd() / dataset_path).resolve()
    if not dataset_path.is_file():
        raise FileNotFoundError(f'Dataset not found: {dataset_path}')

    with dataset_path.open(encoding='utf-8', errors='replace') as dataset_file:
        first_line = dataset_file.readline().strip()
    if first_line == 'version https://git-lfs.github.com/spec/v1':
        raise RuntimeError(
            f'{dataset_path} is a Git LFS pointer, not the dataset. '
            'Run `git lfs pull` from the repository root to download it.'
        )

    return dataset_path
