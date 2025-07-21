from __future__ import annotations
from functools import wraps


def autoFetchProperty(fetch_method_name: str):
    """Decorator for lazy-loading properties with a specified fetch function."""

    def decorator(property_func):
        attr_name = f"_{property_func.__name__}"

        @wraps(property_func)
        def wrapper(self):
            refresh = getattr(self, '__refresh', False)

            # get fetch function
            fetch_func = getattr(self, fetch_method_name, None)

            if fetch_func is None:
                raise AttributeError(f"autoFetchProperty: {self.__class__.__name__} has no method '{fetch_method_name}'")

            flag_name = f"_was{fetch_func.__name__}_called"
            # If already fetched, return the function
            if getattr(self, flag_name, False) and not refresh:
                return property_func(self)

            # Call the fetch function
            if getattr(self, attr_name) is None or refresh:
                print(f"Calling fetch func from within decorator. Attribute: {attr_name}, refresh={refresh}")
                fetch_func()
                # Mark it as fetched
                setattr(self, flag_name, True)

            if refresh:
                # Mark refresh as false after refreshing
                setattr(self, '__refresh', False)

            return property_func(self)

        return wrapper

    return decorator

