import csv
import os
import json
from pathlib import Path
import yaml
from inspect import currentframe
from typing import List, Dict, Tuple, Union, Any
from logging import Logger as Log
from _common import _common as _common_



@_common_.exception_handler
def json_load(filepath: str) -> Union[Dict, List]:
    """
    Loads and parses a JSON file into a Python dictionary or list.

    This function opens a file located at the given filepath, reads its content,
    and then uses json.loads to parse the JSON data into a Python object (either
    a dictionary or a list, depending on the JSON structure).

    Args:
        filepath (str): The path to the JSON file that needs to be loaded.

    Returns:
        Union[Dict, List]: A Python dictionary or list obtained from parsing the JSON file.
        The specific type depends on the JSON structure in the file (object for dict, array for list).

    """
    with open(filepath) as file:
        return json_loads(file.read())


@_common_.exception_handler
def json_loads(data) -> Union[Dict, List]:
    """
    Parses a JSON string into a Python dictionary or list.

    This function takes a string containing JSON data and uses the `json.loads` method
    to convert it into a corresponding Python object. Depending on the structure of the
    JSON data, this could be either a dictionary (for JSON objects) or a list (for JSON arrays).

    Args:
        data: A string containing JSON data.

    Returns:
        Union[Dict, List]: A Python dictionary or list, resulting from parsing the JSON string.
        The specific type depends on the JSON structure in the string (object for dict, array for list).

    """
    return json.loads(data)


@_common_.exception_handler
def json_dumps(data) -> str:
    """
    Converts a Python object (dict or list) to a JSON-formatted string.

    This function takes a Python dictionary or list and serializes it into a JSON-formatted string
    using Python's built-in `json.dumps` method. It can be used to easily convert Python data structures
    to a JSON string format, which can be useful for storing or transmitting data in a standardized format.

    Args:
        data: A Python dictionary or list to be serialized into JSON.

    Returns:
        str: A string representation of the input data in JSON format.

    """
    return json.dumps(data)


@_common_.exception_handler
def json_dump(filepath: str, data) -> None:
    """
    Serializes Python data and writes it to a file in JSON format.

    This function takes a Python data structure (like a dictionary or list) and a file path.
    It serializes the data into a JSON string using `json.dumps` and then writes this string
    to the specified file. This is useful for saving Python data structures in a human-readable
    and standardized JSON format for later retrieval or processing.

    Args:
        filepath: The path to the file where the JSON data should be saved.
        data: The Python data structure (e.g., dict, list) to be serialized into JSON.

    Returns:
        None: This function does not return anything.

    """
    with open(filepath, "w") as file:
        file.write(json.dumps(data))


@_common_.exception_handler
def yaml_load(filepath: str) -> Dict:
    """
    Loads and parses a YAML file into a Python dictionary.

    This function opens a YAML file located at the given filepath and uses the `yaml.safe_load`
    method to parse its content into a Python dictionary. The `safe_load` method is used to
    prevent the execution of arbitrary code that could be present in the YAML file.

    Args:
        filepath: The path to the YAML file that needs to be loaded.

    Returns:
        Dict: A Python dictionary representing the parsed content of the YAML file.

    """
    with open(filepath, "r") as file:
        return yaml.safe_load(file)


@_common_.exception_handler
def yaml_loads(file_content: str) -> Dict:
    """
    Parses a YAML-formatted string into a Python dictionary.

    This function takes a string containing YAML data and uses the `yaml.safe_load` method
    to parse it into a Python dictionary. This is useful for converting YAML content received
    in string format, such as from a text area or an API response, into a usable Python data structure.

    Args:
        file_content: A string containing YAML-formatted data.

    Returns:
        Dict: A Python dictionary representing the parsed content of the YAML string.

    """
    return yaml.safe_load(file_content)


@_common_.exception_handler
def yaml_dumps(file_content) -> str:
    """
    Serializes a Python object into a YAML-formatted string.

    This function takes a Python data structure (such as a dictionary or list) and converts it
    into a YAML-formatted string using the `yaml.dump` method. This is particularly useful for
    converting Python objects into a YAML format for storage, configuration files, or transmitting
    data in a human-readable format.

    Args:
        file_content: The Python data structure to be serialized into YAML. This can be a dictionary,
        list, or any other data type that `yaml.dump` can process.

    Returns:
        str: A string representation of the input data in YAML format.

    """
    return yaml.dump(file_content)


@_common_.exception_handler
def yaml_dump(filepath: str, data: Any) -> bool:
    """
    Serializes and writes a Python object to a file in YAML format.

    This function takes a Python data structure and a file path. It serializes the data
    into a YAML-formatted string using a helper function `yaml_dumps` and then writes
    this string to the file specified by the filepath. After writing, it returns True
    to indicate successful execution.

    Args:
        filepath (str): The path of the file where the YAML data should be written.
        data (Any): The Python data structure (e.g., dict, list, etc.) to be serialized into YAML.

    Returns:
        bool: True, indicating that the function executed successfully and the file was written.

    """
    with open(filepath, "w") as file:
        file.write(yaml_dumps(data))
    return True


@_common_.exception_handler
def files_in_dir(dirpath: str) -> List:
    """
    Retrieves a list of file paths contained within a specified directory and its subdirectories.

    This function walks through the directory specified by 'dirpath', including all its
    subdirectories, and compiles a list of full file paths for each file found. It uses
    the `os.walk` method to traverse the directory tree.

    Args:
        dirpath: The path of the directory to search for files.

    Returns:
        List[str]: A list containing the full paths of all files within the specified directory
        and its subdirectories.

    """
    dirpath = os.path.expanduser(dirpath) if dirpath.startswith("~") else dirpath
    return [os.path.join(_dirpath, f) for (_dirpath, _, _filenames) in os.walk(dirpath) for f in _filenames]


@_common_.exception_handler
def is_file_exist(filepath: str) -> bool:
    """
    Checks whether a file exists at a specified path.

    This function uses Python's pathlib module to determine if a file exists at the given
    file path. It returns True if the file exists, and False otherwise. This is a straightforward
    way to check for the existence of a file without opening or reading the file.

    Args:
        filepath: The path of the file to check for existence.

    Returns:
        bool: True if the file exists at the specified path, False otherwise.

    """
    return Path(filepath).is_file()


@_common_.exception_handler
def write_file(filepath: str, data: Any) -> bool:
    """
    Writes data to a file and returns a success flag.

    This function opens a file at the specified filepath in write mode and writes the provided
    data to it. It is designed to handle any data that can be represented as a string. After writing,
    the function returns True to indicate successful execution.

    Args:
        filepath: The path of the file where the data should be written.
        data: The data to be written to the file. It could be a string or any data type
                    that can be represented as a string.
    Returns:
        bool: True, indicating that the file write operation was successful.

    """
    with open(filepath, "w") as file:
        file.write(data)
    return True


@_common_.exception_handler
def load_file(filepath: str) -> str:
    """
    Reads and returns the entire content of a file as a string.

    This function opens a file located at the given filepath and reads its entire content, returning it as a string.
    It's a convenient way to quickly load and access the contents of a file, especially useful for text files.

    Args:
        filepath: The path of the file to be read.

    Returns:
        str: The entire content of the file as a string.

    """
    with open(filepath) as file:
        return file.read()


# @_common_.exception_handler
# def csv_to_json(filepath: str) -> Union[List, Dict]:
#     """
#     Converts a CSV file to JSON format.
#
#     This function reads a CSV file from the given filepath, converts it to a JSON-formatted string using
#     Pandas, and then parses this string into a Python object (either a list of dictionaries or a dictionary,
#     depending on the structure of the JSON). It's useful for converting CSV data to JSON, often needed for
#     data interchange or API responses.
#
#     Args:
#         filepath: The path of the CSV file to be converted.
#     Returns:
#         Union[List, Dict]: A Python object representing the converted JSON data. The specific type (list or dict)
#         depends on the structure of the JSON.
#
#     """
#     return json_loads(pd.read_csv(filepath).to_json(orient="records"))


@_common_.exception_handler
def json_to_csv(filepath: str, data: Union[List, Dict], header: List = None) -> bool:
    """
    Converts JSON data to CSV format and writes it to a file.

    This function takes JSON data (either in the form of a list of dictionaries or a single dictionary) and
    writes it to a CSV file at the specified filepath. Optionally, a custom header (list of field names) can
    be provided. If no custom header is provided, the field names are inferred from the keys of the first
    dictionary in the data list.

    Args:
        filepath: The path of the file where the CSV data should be written.
        data: The JSON data to be converted into CSV. This can be a list of dictionaries
                                  or a single dictionary.
        header: An optional list of header field names. If provided, these names are used as
                                 the header row of the CSV. If not provided, the keys of the first dictionary
                                 in the data are used. Defaults to None.
    Returns:
        bool: True, indicating that the CSV file was written successfully.

    """
    if header:
        fieldnames = header
    else:
        fieldnames = data[0].keys()

    with open(filepath, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()

        for row in data:
            writer.writerow(row)
    return True


@_common_.exception_handler
def is_file_empty(filepath: str) -> bool:
    """
    Determines whether a specified file is empty.

    This function checks if the file at the given filepath is empty by evaluating its size.
    It first verifies that the file exists and is indeed a file, not a directory. Then it
    checks the file's size. If the size is zero bytes, it returns True, indicating the file
    is empty. Otherwise, it returns False.

    Args:
        filepath: The path of the file to be checked.

    Returns:
        bool: True if the file exists and is empty, False otherwise.

    """
    if os.path.isfile(filepath):
        return os.path.getsize(filepath) == 0
    else:
        return False

@_common_.exception_handler
def find_file(starting_directory: str, filename: str, max_depth: int = None) -> str | None:
    starting_depth = starting_directory.rstrip(os.sep).count(os.sep)  # Get initial depth

    for root, dirs, files in os.walk(starting_directory):
        current_depth = root.rstrip(os.sep).count(os.sep)

        # If max_depth is set, stop recursion beyond allowed depth
        if max_depth is not None and (current_depth - starting_depth) >= max_depth:
            del dirs[:]  # Prevent deeper traversal

        if filename in files:
            return os.path.abspath(os.path.join(root, filename))

    return None  # Return None if file is not found

# def pghtml_to_jira_wiki(filepath: str, logger: Log = None) -> str:
#     try:
#         with open(filepath) as file:
#             return html_to_jira_wiki(file.read())
#
#     except Exception as err:
#         _common_.error_logger(currentframe().f_code.co_name,
#                              err,
#                              logger=logger,
#                              mode="error",
#                              ignore_flag=False)

# _data = ivalidation._parse_data()
#
# #print(_data)
# x = json.loads(_data)
#
# for _item in json.loads(_data):
#     if _item and _item.get("(Disabled) OHH KCI/FCI - TP99 exceeded threshold of 7 seconds", "").startswith("zb_"):
#         print(_item.get("(Disabled) OHH KCI/FCI - TP99 exceeded threshold of 7 seconds"))
#
# exit(0)