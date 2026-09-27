import functools
import inspect

import allure


def step(title: str):
    """Like @allure.step, but records only the step title — never the call's arguments. allure.step
    attaches every argument as a step parameter, and ours carry credentials, tokens and headers."""

    def decorator(func):
        signature = inspect.signature(func)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            with allure.step(title.format(**bound.arguments)):
                return func(*args, **kwargs)

        return wrapper

    return decorator
