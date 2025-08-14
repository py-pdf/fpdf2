from typing import Any, Optional


class Substitution:
    """
    This class binds a placeholder to a specific value.

    You're supposed to use the string representation (e.g. str(x) or f'{x}')
    to put a substitution object in text.

    You must assign a string to the property "value" before "outputting" the PDF,
    so the placeholder will be substituted with this string in the result file.

    You might need to store some related data to compute the substitution value later.
    The "extra_data" property can be used for this.
    """

    __slots__ = ("_placeholder", "_value", "extra_data")

    def __init__(self, placeholder: str, extra_data: Optional[Any] = None):
        self._placeholder = placeholder
        self.value: Optional[str] = None
        self.extra_data = extra_data

    def __str__(self):
        return self._placeholder

    def __setattr__(self, name, value):
        if name == "value" and not (value is None or isinstance(value, str)):
            raise ValueError(
                f"Value must be a string, but it has the type {type(value)}."
            )

        return super().__setattr__(name, value)


class TotalPagesSubstitution(Substitution): ...


class CurrentPageSubstitution(Substitution): ...


class ToCPageSubstitution(Substitution): ...
