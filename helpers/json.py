from pathlib import Path
import json


def save_component_json(data,
                        filename: str,
                        folder: str = "temp_data",
                        encoding: str = "utf-8") -> None:

    """
    save data as a json file under a specific name under a specific folder with a specific encoding
    :param data: Data that should be saved as JSON file
    :param filename: Name of the file to be saved
    :param folder: Name of the folder where the CSV file should be saved
    :param encoding: encoding type
    """
    with open(Path(folder) / f"{filename}.json", "w", encoding=encoding) as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_component_json(filename: str,
                        folder: str = "temp_data",
                        encoding: str = "utf-8"):
    """
    open json file of specific name under specific folder with specific encoding
    :param data: Data that should be saved as JSON file
    :param filename: Name of the file to be saved
    :param folder: Name of the folder where the CSV file should be saved
    :param encoding: encoding type
    """
    with open(Path(folder) / f"{filename}.json", encoding=encoding) as file:
        return json.load(file)
