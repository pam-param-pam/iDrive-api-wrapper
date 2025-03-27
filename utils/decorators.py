from __future__ import annotations

import inspect
import re
from functools import wraps

"""https://stackoverflow.com/questions/1167617/in-python-how-do-i-indicate-im-overriding-a-method
python being goofy, and having no @override decorator LOL"""


def overrides(method):
    # actually can't do this because a method is really just a function while inside a class def'n
    # assert(inspect.ismethod(method))

    stack = inspect.stack()
    base_classes = re.search(r'class.+\((.+)\)\s*\:', stack[2][4][0]).group(1)

    # handle multiple inheritance
    base_classes = [s.strip() for s in base_classes.split(',')]
    if not base_classes:
        raise ValueError('overrides decorator: unable to determine base class')

    # stack[0]=overrides, stack[1]=inside class def'n, stack[2]=outside class def'n
    derived_class_locals = stack[2][0].f_locals

    # replace each class name in base_classes with the actual class type
    for i, base_class in enumerate(base_classes):

        if '.' not in base_class:
            base_classes[i] = derived_class_locals[base_class]

        else:
            components = base_class.split('.')

            # obj is either a module or a class
            obj = derived_class_locals[components[0]]

            for c in components[1:]:
                assert (inspect.ismodule(obj) or inspect.isclass(obj))
                obj = getattr(obj, c)

            base_classes[i] = obj

    assert (any(hasattr(cls, method.__name__) for cls in base_classes)), "Method is not the same as in parent class"
    return method


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
                print("Calling fetch func from within decorator")
                fetch_func()

            # Mark it as fetched
            setattr(self, flag_name, True)

            if refresh:
                # Mark refresh as false after refreshing
                setattr(self, '__refresh', False)

            return property_func(self)

        return wrapper

    return decorator

