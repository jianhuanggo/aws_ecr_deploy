import os
import inspect
import re
import importlib
from inspect import currentframe
from jinja2 import Template

from _logging.pg_logger import get_logger, log_method, error_logger

# Configure the logger
logger = get_logger(
    name="",
    log_level=os.environ.get("LOG_LEVEL", "INFO"),
    log_to_console=True,
    log_to_file=True,
    log_file_path=os.environ.get("LOG_FILE_PATH", "/tmp/ecr_deployment.log")
)


"""

location: /Users/jianhuang/anaconda3/envs/pg_aws_lambda_test/pg_aws_lambda_test
sample main function signature:


---------------------------------------------------------------------
def main(role_arn: str, profile_name: str):
    from _task import _task
    return _task.list_s3_buckets(role_arn=role_arn, profile_name=profile_name)


if __name__ == "__main__":
    print(main(role_arn="arn:aws:iam::717435123117:role/iam-role-lamba-test",
               profile_name="latest"))

"""


def generic_lambda_handler_template():
    template = """import json
{{ from_imports }}

def lambda_handler(event, context):

{{ declare_variables }}
    try:
        query_params = event.get('queryStringParameters', {})
        print(query_params)
{% if variables_extraction %}
        if query_params:
{{ variables_extraction }}
{% endif %}

{% if check_variables %}
{{ check_variables }}
            return {
                    'statusCode': 404,
                    'headers': {
                        'Access-Control-Allow-Headers': '*',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                    },
                    'body': json.dumps("input variable is missing")
            }
{% endif %}


        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({{ return_statement }})
        }

    except Exception as err:
        return {
            'statusCode': 404,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps(f"Something is error while processing, {err}")
        }
    """
    return template

def write_file(filepath: str, data: any) -> bool:
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

def extract_returned_function_name_with_inspect(function: callable) -> str:
    """
    Extracts the function name that is returned in the provided function using inspect.
    """
    # Get the source code of the provided function using inspect
    source_code = inspect.getsource(function)

    # Use a regular expression to search for a return statement that calls a function
    pattern = re.compile(r'return\s+(.+)')  # Adjust this if needed for different cases
    match = pattern.findall(source_code)

    if match:
        # Return the function name (the second part of the matched group)
        return match[0]  # Group 2 contains the method/function name after the dot
    return "No function returned in the main function."

def extract_main_param_with_inspect(function: callable) -> list:
    # Get the signature of the function
    signature = inspect.signature(function)

    # Extract parameter names
    return list(signature.parameters.keys())


def get_function(function_name: str):
    """
    Dynamically load a function from a module.
    """
    # module = importlib.import_module("_code._generate_template")
    # if hasattr(module, function_name):
    #     return getattr(module, function_name)()
    # else:
    #     print(f"No function named {function_name} found in the module.", "FunctionNotFoundError")
    return generic_lambda_handler_template()

def load_module_from_path(module_name, filepath):
    """
    Dynamically load a module from the given file path.
    """

    spec = importlib.util.spec_from_file_location(module_name, filepath)

    print(filepath)


    if spec is None:
        raise ImportError(f"Cannot load the module from the path: {filepath}")

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)
    return module

def apply_template(template: str, params: dict) -> str:
    return Template(template).render(params)

def extract_from_statements(source_code: str):
    """
    Extracts all lines from the source code that start with the keyword 'from'.
    """

    # Regular expression to match lines that start with 'from', ignoring leading spaces
    from_pattern = re.compile(r'^\s*from\s+.+', re.MULTILINE)

    # Find all matches in the source code
    matches = from_pattern.findall(source_code)

    return matches

def convert_lambda_function(declare_variables: str,
                            variables_extraction: str,
                            return_statement: str,
                            check_variables: str,
                            from_imports: str = "",
                            template_name: str = "generic_lambda_handler") -> str:
    lambda_handler_template = get_function(template_name)

    _params = {
        "from_imports": from_imports,
        "declare_variables": declare_variables,
        "variables_extraction": variables_extraction,
        "check_variables": check_variables,
        "return_statement": return_statement
    }
    print("variables_extraction!!!!", variables_extraction.strip())
    print("check_variables!!!!!", check_variables.strip())
    if check_variables.strip() == "if:":
        _params["check_variables"] = None

    return apply_template(lambda_handler_template, _params)


def generate_lambda_handler(filepath: str) -> bool:
    """
    Generate a lambda handler function from a given Python file.
    """

    lambda_handler_filepath = os.path.join(filepath, "lambda_function.py")
    if os.path.isfile(lambda_handler_filepath):
        print(f"lambda_function.py found in {filepath}")
        return True
    else:
        print(f"lambda_function.py does not exists in {filepath}, generating it...")

    module_name = 'main'
    print(os.path.join(filepath, "main.py"))


    module = load_module_from_path(module_name, os.path.join(filepath, "main.py"))

    returned_function_name = ""
    _declare_variables = ""
    _variables_extraction=""
    _from_imports =""
    main_function = None

    # Assuming 'main' is defined in the loaded module
    if hasattr(module, 'main'):
        main_function = getattr(module, 'main')

        # Extract and print the function name returned by the 'main' function
        returned_function_name = extract_returned_function_name_with_inspect(main_function)

        print(f"The function returned in main() is: {returned_function_name}")

    else:
        print(f"No 'main' function found in {filepath}", "MainFunctionNotFoundError")

    _function_params = extract_main_param_with_inspect(main_function)
    print(_function_params)

    _declare_variables = '\n'.join([f"    {param} = None" for param in _function_params])
    _variables_extraction = '\n'.join([f"            {param} = query_params.get('{param}', 'default_value_if_missing')" for param in _function_params])
    _check_variables = "        if" + ' or'.join([f" {param} is None" for param in _function_params]) + ":"

    _from_imports = '\n'.join(extract_from_statements(inspect.getsource(main_function)))
    print(_from_imports)

    write_file(os.path.join(filepath, "lambda_function.py"),
                           convert_lambda_function(declare_variables=_declare_variables,
                                                   variables_extraction=_variables_extraction,
                                                   return_statement=returned_function_name,
                                                   check_variables=_check_variables,
                                                   from_imports=_from_imports.strip())
                           )
    return True