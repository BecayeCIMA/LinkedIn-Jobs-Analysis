import pandas as pd
import numpy as np
from os.path import join

def create_dataframe(list_, colnames):
    df = pd.DataFrame(np.array(list_), columns=colnames)
    return df

def save_to_csv(data, folder, filename='jobs', colnames=None):
    """
    Save data to CSV.

    If a list is passed, we convert it to a dataframe first.
    """
    if isinstance(data, list) and not isinstance(data, pd.DataFrame):
        data = create_dataframe(data, colnames)

    path = join(folder, filename, '.csv')
    data.to_csv(path, encoding='utf-8-sig', index=False)
