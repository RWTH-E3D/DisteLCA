import numpy as np
import pandas


def reorder_dataframe(df: pandas.DataFrame, reordered_column_indexes: list) -> pandas.DataFrame:
    """
    This function enables a quick reordering of the columns in a pandas dataframe (table). The
    current indices of the columns must be entered as a list in the order in which the columns
    are to be reordered. Example: When changing the column with the index 0 with the column with
    the index 1, the following input is required: [1, 0]
    :param df: Pandas dataframe as data source
    :param reordered_column_indexes: list of column indices

    """
    # Create list of column names from data frame
    col = df.columns.values.tolist()
    # Create empty list that will be filled with the names of the columns in the desired order
    new_order = []
    # Fill the list with the column names
    for index in reordered_column_indexes:
        new_order.append(col[index])
    # Return reordered dataframe from list of column names
    return df[new_order]


def pandas_convert_decimals(df: pandas.DataFrame, column: str) -> pandas.DataFrame:
    '''
    This function converts string values in Pandas Dataframes into floats for further data processing.
    :param df: dataframe with columns to be changed to float type
    :param column: column names of the Pandas dataframe to be changed to float type
    :return:
    '''
    # In the life cycle inventory phase, some NaN values were replaced with "-" for a better visualisation
    # These values have to be changed back for float type change of a column
    df[column] = df[column].replace('-', np.nan)
    # Replace the German decimal visualisation
    try:
        df[column] = df[column].str.replace(',', '.').astype({column: float})
    except Exception:
        pass
    return df


def diff_two_dataframes(df1: pandas.DataFrame, df2: pandas.DataFrame) -> pandas.DataFrame:
    '''
    Return only the rows of a dataframe that are not present in another dataframe.
    This function supports the display of the different material masses
    for the remediation scenarios in the life cycle inventory phase.
    This function is used instead of the "drop.duplicates" feature of pandas, as the "drop.duplicates"
    drops all rows that are equal to the row in the smaller dataframe and when there are refurbishment materials with
    the same credentials as existant materials they will be dropped unintentionally.
    :param df1: smaller dataframe
    :param df2: bigger dataframe
    :return: Dataframe difference
    '''
    df2 = df2.copy()
    # Iterate through rows of the smaller dataframe
    for index1, row1 in df1.iterrows():
        # Iterate through rows of the bigger dataframe and check if rows are equal
        for index2, row2 in df2.iterrows():
            if (row1 == row2).all():
                # Drop equal rows
                df2.drop(index2, inplace=True)
                # If an equal row is found, drop it and break the iteration as it only has to be dropped once
                break

    return df2
