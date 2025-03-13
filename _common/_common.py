import os
import time
import functools
import asyncio
from sys import exit
import importlib
from logging import Logger as Log
from time import sleep
from itertools import zip_longest
from functools import wraps
import uuid
from typing import List, Union, Tuple, Callable, Dict, Any, TypeVar
from inspect import currentframe, getmembers, isfunction
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError


RT = TypeVar('RT')  # return type

__version__ = "0.5"

"""
for retry: use retry lib
need a decorator to change 


"""


def info_logger(message: str = "",
                func_str: str = "",
                logger: Log = None,
                addition_msg: str = ""
                ) -> None:
    """Display message in a logger if there is one otherwise stdout
    Args:
        message: display message
        func_str: calling function, so error msg can be associated correctly
        logger: Whether error msg should be persisted in a log file
        addition_msg: A set of parameters which need to be verified
    Returns:
        No return value.
    """
    try:
        if func_str:
            message = f"{func_str}: {message}"
        logger.info(f"{message} {addition_msg}") if logger else print(f"{message} {addition_msg}")

    except Exception as err:
        raise err


def error_logger(func_str: str, error,
                 logger: Log = None,
                 addition_msg: str = "",
                 mode: str = "critical",
                 ignore_flag: bool = True,
                 set_trace: bool = False) -> None:

    def _not_found(*args, **kwargs):
        raise "error mode should be 'critical', 'debug', 'error' and 'info'"
    if logger:
        _logger_mode = {"critical": logger.critical,
                        "debug": logger.debug,
                        "error": logger.error,
                        "info": logger.info
                        }
    try:
        _logger_mode.get(mode, _logger_mode)(f"Error in {func_str} {addition_msg} {error}") if logger \
            else print(f"Error in {func_str} {addition_msg} {error}")
        if logger and set_trace: logger.exception("trace")
        return exit(99) if not ignore_flag else None
    except Exception as err:
        raise err


def string_search(input_string: str, pattern: str, logger: Log = None) -> int:
    """string search based on KPM algorithm

    Parameters:
    :param input_string: there are two versions of code
    :param pattern: search pattern
    :param logger: logger object
    :Returns:
        return the index of the first occurrance, otherwise -1 if not found

   """
    try:
        _b_ptr, _p_ptr, _lpr = 1, 0, [0]
        while _b_ptr < len(pattern):
            if pattern[_b_ptr] == pattern[_p_ptr]:
                _lpr.append(_p_ptr + 1)
                _b_ptr, _p_ptr = _b_ptr + 1, _p_ptr + 1
            elif _p_ptr == 0:
                _lpr.append(0)
                _b_ptr += 1
            else:
                _p_ptr = _lpr[_p_ptr - 1]
        _b_ptr, _p_ptr = 0, 0

        while _b_ptr < len(input_string):
            if input_string[_b_ptr] == pattern[_p_ptr]:
                _b_ptr, _p_ptr = _b_ptr + 1, _p_ptr + 1
            elif _p_ptr == 0:
                _b_ptr += 1
            else:
                _p_ptr = _lpr[_p_ptr - 1]
            if _p_ptr == len(pattern):
                return _b_ptr - len(pattern)
        return -1
    except Exception as err:
        error_logger(currentframe().f_code.co_name,
                     err,
                     logger=logger,
                     mode="error",
                     ignore_flag=False)


def find_relative_path(abs_filepath: str):
    return ''.join([a for a, b in zip_longest(abs_filepath,  os.path.abspath(os.curdir)) if a != b])


def exception_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as err:
            error_logger(
                         #currentframe().f_code.co_name,
                         func.__name__,
                         err,
                         logger=kwargs.get("logger"),
                         mode="error",
                         ignore_flag=False)
    return wrapper


def exception_handlers(logger: Log = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as err:
                error_logger(
                             func.__name__,
                             err,
                             logger=logger,
                             mode="error",
                             ignore_flag=False)
        return wrapper
    return decorator


def get_docstring(marker: str):
    def decorate(func):
        def wrapper(*args, **kwargs):
            docstring = func.__doc__
            if docstring:
                marker_index = docstring.find(marker)
                if marker_index != -1:
                    return docstring[:marker_index].strip()
                else:
                    return docstring.strip()
            else:
                return ""
        return wrapper
    return decorate


@exception_handler
def load_python_module(filepath: str):
    import os
    import importlib.util

    # Given file path

    # Check if the file exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"No such file: '{filepath}'")

    # Extract directory and module name from the file path
    dir_name = os.path.dirname(filepath)
    module_name = os.path.basename(filepath).rstrip('.py')

    # Add the directory to sys.path
    import sys
    sys.path.insert(0, dir_name)

    # Load the module
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


@exception_handler
def add_dirpath(dirpath: str):
    """

    There are multiple methods to "incorporate" a Python module into the main structure. One approach is to install
    it as a library using Python package management tools like conda, pip, or poetry.

    Including the repository at the repository level provides an alternative method to integrate external modules
    into the main structure. This method is favored when modifications to the external module are needed and there is no setup.py required.

    :param github_repo_url: github repo url
    :param logger: logger object
    :return:

    """
    import sys
    from typing import Union
    from types import ModuleType, FunctionType

    def get_file_path_for_module(package_name: Union[ModuleType, FunctionType]):
        import inspect
        file_location = inspect.getfile(package_name)
        print(file_location)

    sys.path.append(dirpath)


def find(package_name):
    from pathlib import Path
    def print_package_contents(package_name):
        # Find the path of the package
        spec = importlib.util.find_spec(package_name)
        if spec is None or spec.origin is None:
            print(f"{package_name} is not a valid package")
            return

        package_path = Path(spec.origin).parent

        # Print the contents of the package directory
        for item in package_path.rglob('*'):
            print(item)
    print_package_contents(package_name)


class AWSsdkError(Exception):
    """Custom exception class for specific error handling."""
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code

    def __str__(self):
        return f"[Error {self.error_code}]: {self.args[0]}"


class NoCredError(AWSsdkError):
    """Exception raised for errors when no credential is found."""
    def __init__(self, message="Error: No AWS credentials found.", error_code=2001):
        super().__init__(message, error_code)


class PartialCredError(AWSsdkError):
    """Exception raised for errors when no credential is found."""
    def __init__(self, message="Error: Incomplete AWS credentials found.", error_code=3001):
        super().__init__(message, error_code)


class UnexpectedError(AWSsdkError):
    """Exception raised for errors when no credential is found."""
    def __init__(self, message, error_code=10001):
        super().__init__(message, error_code)


def aws_handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NoCredentialsError:
            raise NoCredError()
        except PartialCredentialsError:
            raise PartialCredError()
        except ClientError as err:
            if err.response.get("Error", {}).get("Code") == 'InvalidGroup.NotFound':
                info_logger(err)
                return False
            raise UnexpectedError(f"Unexpected error: {err}")
        except Exception as err:
            error_logger(func.__name__,
                         err,
                         logger=None,
                         mode="error",
                         ignore_flag=False)
    return wrapper

class CustomException(Exception):
    pass


class AlwaysFalseException:
    def __getattr__(self, name):
        return self

    def __bool__(self):
        return False


aws_client = AlwaysFalseException()
aws_client.exceptions = AlwaysFalseException()
aws_client.exceptions.NoSuchEntityException = CustomException


class ClientException(Exception):
    def __init__(self, message="An error occurred with the client operation", error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        if self.error_code:
            return f"[Error Code: {self.error_code}] {self.message}"
        return self.message


def aws_client_handle_exceptions(not_found_code: str = "", aws_client_exception=ClientException, logger: Log = None):
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except aws_client_exception:
                info_logger(f"warning:  in function {func.__name__}, encounter {aws_client_exception}")
            # except aws_client.exceptions.NoSuchEntityException:
            #     info_logger(f"warning:  in function {func.__name__}, encounter {aws_client.exceptions.NoSuchEntityException}")
            except NoCredentialsError:
                raise NoCredError()
            except PartialCredentialsError:
                raise PartialCredError()
            except ClientError as err:
                if err.response.get("Error", {}).get("Code") == not_found_code:
                    info_logger(f"warning: in function {func.__name__}, encounter {not_found_code}")
                    return False
                raise UnexpectedError(f"Unexpected error: {err}")
            except Exception as err:
                error_logger(func.__name__,
                             err,
                             logger=None,
                             mode="error",
                             ignore_flag=False)
        return wrapper
    return decorate



# def aws_error_logger(func_str: str,
#                      error,
#                      logger: Log = None,
#                      addition_msg: str = "",
#                      mode: str = "critical",
#                      ignore_flag: bool = True,
#                      set_trace: bool = False) -> None:
#     """Display error message in a logger if there is one otherwise stdout
#     Args:
#         func_str: calling function, so error msg can be associated correctly
#         error: exception captured
#         logger: Whether error msg should be persisted in a log file
#         addition_msg: A set of parameters which need to be verified
#         mode: error mode, either critical, debug, error or info
#         ignore_flag: It will return to the calling function if set to True otherwise program will terminate
#         set_trace: This will log stack trace
#     Returns:
#         No return value.
#     """
#     def _not_found(*args, **kwargs):
#         raise "error mode should be 'critical', 'debug', 'error' and 'info'"
#     if logger:
#         _log_mode = {"critical": logger.critical,
#                      "debug": logger.debug,
#                      "error": logger.error,
#                      "info": logger.info}
#     try:
#         _log_mode.get(mode, _not_found)(f"Error in {func_str}! {addition_msg} {error}") if logger \
#             else print(f"Error in {func_str}! {addition_msg} {error}")
#         if logger and set_trace:
#             logger.exception("trace")
#         return exit(99) if not ignore_flag else None
#     except Exception as err:
#         raise err