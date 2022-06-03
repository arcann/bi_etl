import inspect
from pathlib import Path


def get_package_root_path(obj: object = None) -> Path:
    """
    Get the root path of a package given an object (default is this module).

    Parameters
    ----------
    obj:
        The object to inspect for package. Defaults to this module

    Returns
    -------
        The root path of the package as a pathlib.Path
    """
    if obj is None:
        obj = get_package_root_path
    module_path = Path(inspect.getfile(obj))
    return module_path.parents[1]


def get_package_root_str(obj: object = None) -> str:
    """
    Get the root path of a package given an object (default is this module).

    Parameters
    ----------
    obj:
        The object to inspect for package. Defaults to this module

    Returns
    -------
        The root path of the package as a string
    """
    return str(get_package_root_path(obj))


if __name__ == '__main__':
    print(get_package_root_str())
