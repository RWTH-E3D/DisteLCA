import pandas
import plotly.graph_objects as go
import numpy as np
np.random.seed(1)

def create_table(df: pandas.DataFrame, directory: str) -> None:
    df.to_csv(directory + '.csv', index=False)


