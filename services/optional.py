import logging
from functools import wraps
from typing import Callable, Optional, TypeVar, Generic, Union


class InputValidationError(ValueError):
    pass


A = TypeVar('A')


class ExceptionalOptional(Generic[A]):
    """
    Pun intended 
    """

    def __init__(self, value: Union[A, BaseException]):
        self._value = value

    def __bool__(self):
        return not self.failed

    @property
    def failed(self) -> bool:
        return isinstance(self._value, BaseException)

    @property
    def value(self) -> A:
        if self.failed:
            raise RuntimeError('trying to get a failed value')
        return self._value

    @property
    def exception(self) -> Optional[BaseException]:
        return self._value if self.failed else None


def fallible(*exceptions, logger=None) \
        -> Callable[[Callable[..., A]], Callable[..., Optional[A]]]:
    """
    :param exceptions: a list of exceptions to catch
    :param logger: pass a custom logger; None means the default logger,
                   False disables logging altogether.
    """
    def fwrap(f: Callable[..., A]) -> Callable[..., ExceptionalOptional[A]]:

        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return ExceptionalOptional(f(*args, **kwargs))
            except exceptions as err:
                message = f'called {f} with *args={args} and **kwargs={kwargs}'
                if logger:
                    logger.exception(message)
                if logger is None:
                    logging.exception(message)
                return ExceptionalOptional(err)

        return wrapped

    return fwrap


if __name__ == '__main__':
    raise RuntimeError
