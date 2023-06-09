from __future__ import annotations
import csv
from pathlib import Path

def save_elca_csv(csv_components: list[dict],
                  filename: str,
                  folder: str = "temp_data") -> None:

    """
    This function creates a csv file from a list of dictionaries.
    This CSV file follows the requirements of eLCA to create
    a project via CSV import. Each list object represents a row of the CSV file.
    The column names are predefined by eLCA.
    :param csv_components: List of dictionaries where every list object represents one csv row and the
            dictionary keys represent the columns
    :param filename: Name of the file to be saved
    :param folder: Name of the folder where the CSV file should be saved
    """
    filtered_csv_components = [csv_component for csv_component in csv_components if csv_component != None]
    # Create CSV file
    with open(Path(folder) / f"{filename}.csv", 'w', newline='', encoding='utf-8') as file:
        # Column names required for csv-Import in eLCA
        fieldnames = ['Name', 'KG DIN 276', 'Fläche', 'Bezugsgröße', 'eLCA BT ID']
        # eLCA requires semicolon as delimiter
        thewriter = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
        thewriter.writeheader()
        # Iterate through list to append rows
        for component in filtered_csv_components:
            thewriter.writerow(component)