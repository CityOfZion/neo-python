import importlib


def load_class_from_path(path_and_class: str):
    """
    Dynamically load a class from a module at the specified path

    Args:
        path_and_class: relative path where to find the module and its class name
        i.e. 'neo.<package>.<package>.<module>.<class name>'

    Raises:
        ValueError: if the Module or Class is not found.

    Returns:
        class object
    """
    try:
        module_path = '.'.join(path_and_class.split('.')[:-1])
        module = importlib.import_module(module_path)
    except ImportError as err:
        raise ValueError(f"Failed to import module {module_path} with error: {err}")

    try:
        class_name = path_and_class.split('.')[-1]
        class_obj = getattr(module, class_name)
        return class_obj
    except AttributeError as err:
        raise ValueError(f"Failed to get class {class_name} with error: {err}")
