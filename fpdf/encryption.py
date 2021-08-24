from typing import Any, Dict, NamedTuple
from typing import (
    Any,
    BinaryIO,
    Callable,
    Collection,
    Dict,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    List,
    MutableMapping,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    overload,
)
from enum import Enum
from pathlib import Path

class StreamDecodeLevel(Enum):
    all: int = ...
    generalized: int = ...
    none: int = ...
    specialized: int = ...

class ObjectStreamMode(Enum):
    disable: int = ...
    generate: int = ...
    preserve: int = ...

class Permissions(NamedTuple):
    accessibility: bool = True
    extract: bool = True
    modify_annotation: bool = True
    modify_assembly: bool = False
    modify_form: bool = True
    modify_other: bool = True
    print_lowres: bool = True
    print_highres: bool = True


class EncryptionInfo:

    def __init__(self, encdict: Dict[str, Any]):
        self._encdict = encdict

    @property
    def R(self) -> int:
        return self._encdict['R']

    @property
    def V(self) -> int:
        return self._encdict['V']

    @property
    def P(self) -> int:
        return self._encdict['P']

    @property
    def stream_method(self) -> str:
        return self._encdict['stream']

    @property
    def string_method(self) -> str:
        return self._encdict['string']

    @property
    def file_method(self) -> str:
        return self._encdict['file']

    @property
    def user_password(self) -> bytes:
        return self._encdict['user_passwd']

    @property
    def encryption_key(self) -> bytes:
        return self._encdict['encryption_key']

    @property
    def bits(self) -> int:
        return len(self._encdict['encryption_key']) * 8




class Encryption(dict):
    def __init__(
            self,
            *,
            owner: str,
            user: str,
            R: int = 6,
            allow: Permissions = Permissions(),
            aes: bool = True,
            metadata: bool = True,
    ):
        super().__init__()
        self.update(
            dict(R=R, owner=owner, user=user, allow=allow, aes=aes, metadata=metadata)
        )

    @staticmethod
    def open(
            filename_or_stream: Union[Path, str, BinaryIO],
            *,
            password: Union[str, bytes] = "",
            hex_password: bool = False,
            ignore_xref_streams: bool = False,
            suppress_warnings: bool = True,
            attempt_recovery: bool = True,
            inherit_page_attributes: bool = True,
            # access_mode: AccessMode = AccessMode.default,
            allow_overwriting_input: bool = False,
    ) -> 'Pdf': ...

    @property
    def encryption(self) -> EncryptionInfo: ...

    def save(
        self,
        filename_or_stream: Union[Path, str, BinaryIO, None] = None,
        *,
        static_id: bool = False,
        preserve_pdfa: bool = True,
        min_version: Union[str, Tuple[str, int]] = "",
        force_version: Union[str, Tuple[str, int]] = "",
        fix_metadata_version: bool = True,
        compress_streams: bool = True,
        stream_decode_level: Optional[StreamDecodeLevel] = None,
        object_stream_mode: ObjectStreamMode = ObjectStreamMode.preserve,
        normalize_content: bool = False,
        linearize: bool = False,
        qdf: bool = False,
        progress: Callable[[int], None] = None,
        encryption: Optional[Union[Encryption, bool]] = None,
        recompress_flate: bool = False,
    ) -> None: ...


# class StreamDecodeLevel(Enum):
#     all: int = ...
#     generalized: int = ...
#     none: int = ...
#     specialized: int = ...
#
# class ObjectStreamMode(Enum):
#     disable: int = ...
#     generate: int = ...
#     preserve: int = ...

# class Pdf:
#     @staticmethod
#     def open(
#         filename_or_stream: Union[Path, str, BinaryIO],
#         *,
#         password: Union[str, bytes] = "",
#         hex_password: bool = False,
#         ignore_xref_streams: bool = False,
#         suppress_warnings: bool = True,
#         attempt_recovery: bool = True,
#         inherit_page_attributes: bool = True,
#         # access_mode: AccessMode = AccessMode.default,
#         allow_overwriting_input: bool = False,
#     ) -> 'Pdf': ...
#     def save(
#         self,
#         filename_or_stream: Union[Path, str, BinaryIO, None] = None,
#         *,
#         static_id: bool = False,
#         preserve_pdfa: bool = True,
#         min_version: Union[str, Tuple[str, int]] = "",
#         force_version: Union[str, Tuple[str, int]] = "",
#         fix_metadata_version: bool = True,
#         compress_streams: bool = True,
#         stream_decode_level: Optional[StreamDecodeLevel] = None,
#         object_stream_mode: ObjectStreamMode = ObjectStreamMode.preserve,
#         normalize_content: bool = False,
#         linearize: bool = False,
#         qdf: bool = False,
#         progress: Callable[[int], None] = None,
#         encryption: Optional[Union[Encryption, bool]] = None,
#         recompress_flate: bool = False,
#     ) -> None: ...
#     @property
#     def encryption(self) -> EncryptionInfo: ...
