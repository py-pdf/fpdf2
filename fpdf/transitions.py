"""
Usage documentation at: <https://py-pdf.github.io/fpdf2/Presentations.html#transitions>
"""

from abc import ABC
from typing import TYPE_CHECKING, Optional, TypeVar

if TYPE_CHECKING:
    from .encryption import StandardSecurityHandler

_AngleT = TypeVar("_AngleT", int, Optional[int])


class Transition(ABC):
    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        raise NotImplementedError

    @staticmethod
    def _check_dimension(dimension: str) -> str:
        "Return `dimension` if it is H(orizontal) or V(ertical), else raise ValueError"
        if dimension not in ("H", "V"):
            raise ValueError(
                f"Unsupported dimension '{dimension}', must be H(horizontal) or V(ertical)"
            )
        return dimension

    @staticmethod
    def _check_motion(direction: str) -> str:
        "Return `direction` if it is I(nward) or O(utward), else raise ValueError"
        if direction not in ("I", "O"):
            raise ValueError(
                f"Unsupported direction '{direction}', must be I(nward) or O(utward)"
            )
        return direction

    @staticmethod
    def _check_angle(direction: _AngleT, allowed: tuple[_AngleT, ...]) -> _AngleT:
        "Return `direction` if it is one of the `allowed` angles, else raise ValueError"
        if direction not in allowed:
            *others, last = allowed
            choices = f"{', '.join(str(angle) for angle in others)} or {last}"
            raise ValueError(f"Unsupported direction '{direction}', must {choices}")
        return direction


class SplitTransition(Transition):
    def __init__(self, dimension: str, direction: str) -> None:
        self.dimension = self._check_dimension(dimension)
        self.direction = self._check_motion(direction)

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        return f"<</Type /Trans /S /Split /DM /{self.dimension} /M /{self.direction}>>"


class BlindsTransition(Transition):
    def __init__(self, dimension: str) -> None:
        self.dimension = self._check_dimension(dimension)

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        return f"<</Type /Trans /S /Blinds /DM /{self.dimension}>>"


class BoxTransition(Transition):
    def __init__(self, direction: str) -> None:
        self.direction = self._check_motion(direction)

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        return f"<</Type /Trans /S /Blinds /M /{self.direction}>>"


class WipeTransition(Transition):
    def __init__(self, direction: int) -> None:
        self.direction = self._check_angle(direction, (0, 90, 180, 270))

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        return f"<</Type /Trans /S /Wipe /Di /{self.direction}>>"


class DissolveTransition(Transition):
    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        return "<</Type /Trans /S /Dissolve>>"


class GlitterTransition(Transition):
    def __init__(self, direction: int) -> None:
        self.direction = self._check_angle(direction, (0, 270, 315))

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        return f"<</Type /Trans /S /Glitter /Di /{self.direction}>>"


class FlyTransition(Transition):
    def __init__(self, dimension: str, direction: Optional[int] = None) -> None:
        self.dimension = self._check_dimension(dimension)
        self.direction = self._check_angle(direction, (0, 270, None))

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        return (
            f"<</Type /Trans /S /Glitter /M /{self.dimension} /Di /{self.direction}>>"
        )


class PushTransition(Transition):
    def __init__(self, direction: int) -> None:
        self.direction = self._check_angle(direction, (0, 270))

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        return f"<</Type /Trans /S /Push /Di /{self.direction}>>"


class CoverTransition(Transition):
    def __init__(self, direction: int) -> None:
        self.direction = self._check_angle(direction, (0, 270))

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        return f"<</Type /Trans /S /Cover /Di /{self.direction}>>"


class UncoverTransition(Transition):
    def __init__(self, direction: int) -> None:
        self.direction = self._check_angle(direction, (0, 270))

    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        return f"<</Type /Trans /S /Uncover /Di /{self.direction}>>"


class FadeTransition(Transition):
    def serialize(
        self,
        _security_handler: Optional["StandardSecurityHandler"] = None,
        _obj_id: Optional[int] = None,
    ) -> str:
        return "<</Type /Fade /S /Dissolve>>"
