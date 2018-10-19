from pathlib import Path

import pandas as pd

_data_path = Path(__file__).parent / 'data'
required_levels = pd.read_csv(_data_path / 'required_levels.csv')
