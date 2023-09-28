"""
Utilities to perform encryption following the PDF standards.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

import hashlib
import logging
import math
import stringprep
import unicodedata
from binascii import hexlify
from codecs import BOM_UTF16_BE
from os import urandom
from typing import Callable, Iterable, Type, Union

from .enums import AccessPermission, EncryptionMethod
from .errors import FPDFException
from .syntax import Name, PDFObject, PDFString, build_obj_dict
from .syntax import create_dictionary_string as pdf_dict

# try to use cryptography for AES encryption
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, modes
    from cryptography.hazmat.primitives.ciphers.algorithms import AES128, AES256
    from cryptography.hazmat.primitives.padding import PKCS7

    import_error = None
except ImportError as error:
    import_error = error


LOGGER = logging.getLogger(__name__)


class ARC4:
    """
    This is a simplified version of the ARC4 (alleged RC4) algorithm,
    created based on the following sources:
    * Wikipedia article on RC4
    * github.com/manojpandey/rc4 (MIT License)
    * http://people.csail.mit.edu/rivest/pubs/RS14.pdf

    Having this ARC4 implementation makes it possible to have basic
    encryption functions without additional dependencies
    """

    MOD = 256

    def KSA(self, key: bytes) -> list:
        key_length = len(key)
        S = list(range(self.MOD))
        j = 0
        for i in range(self.MOD):
            j = (j + S[i] + key[i % key_length]) % self.MOD
            S[i], S[j] = S[j], S[i]
        return S

    def PRGA(self, S: list) -> Iterable[int]:
        i = 0
        j = 0
        while True:
            i = (i + 1) % self.MOD
            j = (j + S[i]) % self.MOD
            S[i], S[j] = S[j], S[i]
            K = S[(S[i] + S[j]) % self.MOD]
            yield K

    def encrypt(self, key: bytes, text: Union[bytes, bytearray]) -> list:
        keystream = self.PRGA(self.KSA(key))
        res = []
        for c in text:
            res.append(c ^ next(keystream))
        return res


class CryptFilter:
    """Represents one crypt filter, listed under CF inside the encryption dictionary"""

    def __init__(self, mode: str, length: int) -> None:
        super().__init__()
        self.type = Name("CryptFilter")
        self.c_f_m = Name(mode)
        self.length = int(length / 8)

    def serialize(self) -> str:
        obj_dict = build_obj_dict({key: getattr(self, key) for key in dir(self)})
        return pdf_dict(obj_dict)


class EncryptionDictionary(PDFObject):
    """
    This class represents an encryption dictionary
    PDF 32000 reference - Table 20
    The PDF trailer must reference this object (/Encrypt)
    """

    def __init__(self, security_handler: "StandardSecurityHandler") -> None:
        super().__init__()
        self.filter = Name("Standard")
        self.length = security_handler.key_length
        self.r = security_handler.revision
        self.o = f"<{security_handler.o.upper()}>"
        self.u = f"<{security_handler.u.upper()}>"
        if security_handler.revision == 6:
            self.o_e = f"<{security_handler.oe.upper()}>"
            self.u_e = f"<{security_handler.ue.upper()}>"
            self.perms = f"<{security_handler.perms.upper()}>"
        self.v = security_handler.version
        self.p = int32(security_handler.access_permission)
        if not security_handler.encrypt_metadata:
            self.encrypt_metadata = "false"
        if security_handler.cf:
            self.c_f = pdf_dict({"/StdCF": security_handler.cf.serialize()})
        if security_handler.encryption_method == EncryptionMethod.NO_ENCRYPTION:
            self.stm_f = Name("Identity")  # crypt filter for streams
            self.str_f = Name("Identity")  # crypt filter for strings
        else:
            self.stm_f = Name("StdCF")  # crypt filter for streams
            self.str_f = Name("StdCF")  # crypt filter for strings


class StandardSecurityHandler:
    """
    This class is referenced in the main PDF class and is used to handle all encryption functions
        * Calculate password and hashes
        * Provide encrypt method to be called by stream and strings
        * Set the access permissions on the document
    """

    DEFAULT_PADDING = (
        b"(\xbfN^Nu\x8aAd\x00NV\xff\xfa\x01\x08..\x00\xb6\xd0h>\x80/\x0c\xa9\xfedSiz"
    )

    def __init__(
        self,
        fpdf,
        owner_password: str,
        user_password: Union[str, None] = None,
        permission: AccessPermission = AccessPermission.all(),
        encryption_method: EncryptionMethod = EncryptionMethod.RC4,
        encrypt_metadata: bool = False,
    ):
        self.fpdf = fpdf
        self.access_permission = (
            0b11111111111111111111000011000000
            if permission is None
            else (0b11111111111111111111000011000000 | permission)
        )
        self.owner_password = owner_password
        self.user_password = user_password if user_password else ""
        self.encryption_method = encryption_method
        self.cf = None
        self.key_length = 128

        if import_error and self.encryption_method in (
            EncryptionMethod.AES_128,
            EncryptionMethod.AES_256,
        ):
            raise EnvironmentError(
                "cryptography module not available"
                " - Try: 'pip install cryptography' or use RC4 encryption method"
                f" - Import error was: {import_error}"
            )
        if self.encryption_method == EncryptionMethod.AES_128:
            self.version = 4
            self.revision = 4
            fpdf._set_min_pdf_version("1.6")
            self.cf = CryptFilter(mode="AESV2", length=self.key_length)
        elif self.encryption_method == EncryptionMethod.AES_256:
            self.version = 5
            self.revision = 6
            fpdf._set_min_pdf_version("2.0")
            self.key_length = 256
            self.cf = CryptFilter(mode="AESV3", length=self.key_length)
        elif self.encryption_method == EncryptionMethod.NO_ENCRYPTION:
            self.version = 4
            self.revision = 4
            fpdf._set_min_pdf_version("1.6")
            self.cf = CryptFilter(mode="V2", length=self.key_length)
        else:
            self.version = 2
            self.revision = 3
            fpdf._set_min_pdf_version("1.5")
            # not including crypt filter because it's only required on V=4
            # if needed, it would be CryptFilter(mode=V2)

        self.encrypt_metadata = encrypt_metadata

    def generate_passwords(self, file_id: str) -> None:
        """File_id is the first hash of the PDF file id"""
        self.file_id = file_id
        self.info_id = file_id[1:33]
        if self.revision == 6:
            self.k = self.get_random_bytes(32)
            self.generate_user_password_rev6()
            self.generate_owner_password_rev6()
            self.generate_perms_rev6()
        else:
            self.o = self.generate_owner_password()
            self.k = self.generate_encryption_key()
            self.u = self.generate_user_password()

    def get_encryption_obj(self) -> EncryptionDictionary:
        """Return an encryption dictionary"""
        return EncryptionDictionary(self)

    def encrypt(
        self, text: Union[str, bytearray, bytes], obj_id: int
    ) -> Union[str, bytes]:
        """Method invoked by PDFObject and PDFContentStream to encrypt strings and streams"""
        LOGGER.debug("Encrypting %s", text)
        return (
            self.encrypt_stream(text, obj_id)
            if isinstance(text, (bytearray, bytes))
            else self.encrypt_string(text, obj_id)
        )

    def encrypt_string(self, string: str, obj_id: int) -> str:
        if self.encryption_method == EncryptionMethod.NO_ENCRYPTION:
            return PDFString(string, encrypt=False).serialize()
        LOGGER.debug("Encrypting string: %s", string)
        try:
            string.encode("latin-1")
            return f"<{bytes(self.encrypt_bytes(string.encode('latin-1'), obj_id)).hex().upper()}>"
        except UnicodeEncodeError:
            return f'<{hexlify(bytearray(self.encrypt_bytes(BOM_UTF16_BE + string.encode("utf-16-be"), obj_id))).decode("latin-1")}>'

    def encrypt_stream(self, stream: bytes, obj_id: int) -> bytes:
        if self.encryption_method == EncryptionMethod.NO_ENCRYPTION:
            return stream
        return bytes(self.encrypt_bytes(stream, obj_id))

    def is_aes_algorithm(self) -> bool:
        return self.encryption_method in (
            EncryptionMethod.AES_128,
            EncryptionMethod.AES_256,
        )

    def encrypt_bytes(self, data: bytes, obj_id: int):
        """
        PDF32000 reference - Algorithm 1: Encryption of data using the RC4 or AES algorithms
        Append object ID and generation ID to the key and encrypt the data
        Generation ID is fixed as 0. Will need to revisit if the application start changing generation ID
        """
        h = hashlib.new("md5", usedforsecurity=False)
        h.update(self.k)
        h.update(
            (obj_id & 0xFFFFFF).to_bytes(3, byteorder="little", signed=False)
        )  # object id
        h.update(
            (0 & 0xFFFF).to_bytes(2, byteorder="little", signed=False)
        )  # generation id
        if self.is_aes_algorithm():
            h.update(bytes([0x73, 0x41, 0x6C, 0x54]))  # add salt (sAlT) for AES
        key = h.digest()

        if self.is_aes_algorithm():
            return self.encrypt_AES_cryptography(key, data)
        return ARC4().encrypt(key, data)

    def encrypt_AES_cryptography(self, key: bytes, data: bytes) -> bytes:
        """Encrypts an array of bytes using AES algorithms (AES 128 or AES 256)"""
        iv = bytearray(self.get_random_bytes(16))
        padder = PKCS7(128).padder()
        padded_data = padder.update(data)
        padded_data += padder.finalize()
        cipher = (
            Cipher(AES128(key), modes.CBC(iv))
            if self.encryption_method == EncryptionMethod.AES_128
            else Cipher(AES256(self.k), modes.CBC(iv))
        )
        encryptor = cipher.encryptor()
        data = encryptor.update(padded_data) + encryptor.finalize()
        iv.extend(data)
        return iv

    @classmethod
    def get_random_bytes(cls: Type["StandardSecurityHandler"], size: int) -> bytes:
        """
        https://docs.python.org/3/library/os.html#os.urandom
        os.urandom will use OS-specific sources to generate random bytes
        suitable for cryptographic use
        """
        return urandom(size)

    @classmethod
    def prepare_string(cls: Type["StandardSecurityHandler"], string: str) -> bytes:
        """
        PDF2.0 - ISO 32000-2:2020
        All passwords for revision 6 shall be based on Unicode. Preprocessing of a user-provided password
        consists first of normalizing its representation by applying the "SASLPrep" profile (Internet RFC 4013)
        of the "stringprep" algorithm (Internet RFC 3454) to the supplied password using the Normalize and BiDi
        options. Next, the password string shall be converted to UTF-8 encoding, and then truncated to the
        first 127 bytes if the string is longer than 127 bytes

        Python offers a stringprep module with the tables mapped in methods
        """

        # Mapping
        def char_map(char: str) -> str:
            if not char:
                return ""
            # Commonly mapped to nothing
            if stringprep.in_table_b1(char):
                return ""
            # Map non-ascii space characters to space
            if stringprep.in_table_c12(char):
                return "\u0020"
            return char

        if len(string) < 1:
            return bytes()

        prepared_string = "".join(char_map(c) for c in string)

        # Normalization - applies Unicode normalization form KC
        prepared_string = unicodedata.ucd_3_2_0.normalize("NFKC", prepared_string)

        # Prohibited output - RCF4013 2.3
        def is_prohibited(char: str) -> bool:
            return (
                stringprep.in_table_c12(char)  # Non-ASCII space characters
                or stringprep.in_table_c21_c22(char)  # Control characters
                or stringprep.in_table_c3(char)  # Private use
                or stringprep.in_table_c4(char)  # Non-character code points
                or stringprep.in_table_c5(char)  # Surrogate codes
                or stringprep.in_table_c6(char)  # Inappropriate for plain text
                or stringprep.in_table_c7(
                    char
                )  # Inappropriate for canonical representation
                or stringprep.in_table_c8(
                    char
                )  # Change display properties or are deprecated
                or stringprep.in_table_c9(char)  # Tagging characters
            )

        for char in prepared_string:
            if is_prohibited(char):
                raise FPDFException(
                    f"The password {string} contains prohibited characters"
                )

        # Bidirectional characters
        def has_character(string: str, fun: Callable) -> bool:
            return any(fun(char) for char in string)

        if has_character(prepared_string, stringprep.in_table_d1):
            # If a string contains any RandALCat character, the string MUST NOT contain any LCat character.
            if has_character(prepared_string, stringprep.in_table_d2):
                raise FPDFException(
                    f"The password {string} contains invalid bidirectional characters."
                )
            # If a string contains any RandALCat character, a RandALCat character MUST be the first character
            # of the string, and a RandALCat character MUST be the last character of the string.
            if not (
                stringprep.in_table_d1(prepared_string[0])
                and stringprep.in_table_d1(prepared_string[-1])
            ):
                raise FPDFException(
                    f"The password {string} contains invalid bidirectional characters."
                )

        if len(prepared_string) > 127:
            prepared_string = prepared_string[:127]

        return prepared_string.encode("UTF-8")

    def padded_password(self, password: str) -> bytearray:
        """
        PDF32000 reference - Algorithm 2: Computing an encryption key
        Step (a) - Add the default padding at the end of provided password to make it 32 bit long
        """
        if len(password) > 32:
            password = password[:32]
        p = bytearray(password.encode("latin1"))
        p.extend(self.DEFAULT_PADDING[: (32 - len(p))])
        return p

    def generate_owner_password(self) -> str:
        """
        PDF32000 reference - Algorithm 3: Computing the encryption dictionary's O (owner password) value
        The security handler is only using revision 3 or 4, so the legacy r2 version is not implemented here
        """
        m = self.padded_password(self.owner_password)
        for _ in range(51):
            m = md5(m)
        rc4key = m[: (math.ceil(self.key_length / 8))]
        result = self.padded_password(self.user_password)
        for i in range(20):
            new_key = []
            for k in rc4key:
                new_key.append(k ^ i)
            result = ARC4().encrypt(bytes(new_key), result)
        return bytes(result).hex()

    def generate_user_password(self) -> str:
        """
        PDF32000 reference - Algorithm 5: Computing the encryption dictionary's U (user password) value
        The security handler is only using revision 3 or 4, so the legacy r2 version is not implemented here
        """
        m = hashlib.new("md5", usedforsecurity=False)
        m.update(bytearray(self.DEFAULT_PADDING))
        m.update(bytes.fromhex(self.info_id))
        result = bytearray(m.digest())
        key = self.k
        for i in range(20):
            new_key = []
            for k in key:
                new_key.append(k ^ i)
            result = ARC4().encrypt(bytes(new_key), result)
        result.extend(
            (result[x] ^ self.DEFAULT_PADDING[x]) for x in range(16)
        )  # add 16 bytes of random padding
        return bytes(result).hex()

    @classmethod
    def compute_hash(
        cls: Type["StandardSecurityHandler"],
        input_password: bytes,
        salt: bytes,
        user_key: bytes = bytearray(),
    ) -> bytes:
        """
        Algorithm 2B - section 7.6.4.3.4 of the ISO 32000-2:2020
        Applied on Security handlers revision 6
        """
        k = hashlib.sha256(input_password + salt + user_key).digest()
        round_number = 0
        while True:
            round_number += 1
            k1 = input_password + k + user_key
            # Step (a + b)
            cipher = Cipher(AES128(k[:16]), modes.CBC(k[16:32]))
            encryptor = cipher.encryptor()
            e = encryptor.update(k1 * 64) + encryptor.finalize()
            # Step (c)
            # remainder = int.from_bytes(e[:16], byteorder="big") % 3
            remainder = sum(e[:16]) % 3
            # Step (d)
            if remainder == 0:
                k = hashlib.sha256(e).digest()
            elif remainder == 1:
                k = hashlib.sha384(e).digest()
            else:
                k = hashlib.sha512(e).digest()
            # Step (e)
            if round_number >= 64 and e[-1] <= round_number - 32:
                break

        return k[:32]

    def generate_user_password_rev6(self) -> None:
        """
        Generating the U (user password) and UE (user encryption)
        for security handlers of revision 6
        Algorithm 8 - Section 7.6.4.4.7 of the ISO 32000-2:2020
        """
        user_password = self.prepare_string(self.user_password)
        if not user_password:
            user_password = bytearray()
        user_validation_salt = self.get_random_bytes(8)
        user_key_salt = self.get_random_bytes(8)
        u = (
            self.compute_hash(input_password=user_password, salt=user_validation_salt)
            + user_validation_salt
            + user_key_salt
        )
        self.u = u.hex()

        key = self.compute_hash(input_password=user_password, salt=user_key_salt)
        cipher = Cipher(AES256(key), modes.CBC(b"\x00" * 16))
        encryptor = cipher.encryptor()
        ue = encryptor.update(self.k) + encryptor.finalize()
        self.ue = ue.hex()

    def generate_owner_password_rev6(self) -> None:
        """
        Generating the O (owner password) and OE (owner encryption)
        for security handlers of revision 6
        Algorithm 9 - Section 7.6.4.4.8 of the ISO 32000-2:2020
        """
        owner_password = self.prepare_string(self.owner_password)
        if not owner_password:
            raise FPDFException(f"Invalid owner password {self.owner_password}")
        owner_validation_salt = self.get_random_bytes(8)
        owner_key_salt = self.get_random_bytes(8)
        o = (
            self.compute_hash(
                input_password=owner_password,
                salt=owner_validation_salt,
                user_key=bytes.fromhex(self.u),
            )
            + owner_validation_salt
            + owner_key_salt
        )
        self.o = o.hex()

        key = self.compute_hash(
            input_password=owner_password,
            salt=owner_key_salt,
            user_key=bytes.fromhex(self.u),
        )

        cipher = Cipher(AES256(key), modes.CBC(b"\x00" * 16))
        encryptor = cipher.encryptor()
        oe = encryptor.update(self.k) + encryptor.finalize()
        self.oe = oe.hex()

    def generate_perms_rev6(self) -> None:
        """
        7.6.4.4.9 Algorithm 10: Computing the encryption dictionary’s Perms (permissions) value
        (Security handlers of revision 6) of the ISO 32000-2:2020
        """
        perms64b = 0xFFFFFFFF00000000 | self.access_permission
        encrypt_metadata = b"T" if self.encrypt_metadata else b"F"
        perms_input = (
            perms64b.to_bytes(8, byteorder="little", signed=False)
            + encrypt_metadata
            + b"adb"
            + self.get_random_bytes(4)
        )
        # nosemgrep: python.cryptography.security.insecure-cipher-mode-ecb.insecure-cipher-mode-ecb
        cipher = Cipher(AES256(self.k), modes.ECB())
        encryptor = cipher.encryptor()
        perms = encryptor.update(perms_input) + encryptor.finalize()
        self.perms = perms.hex()

    def generate_encryption_key(self) -> bytes:
        """
        PDF32000 reference
        Algorithm 2: Computing an encryption key
        """
        m = hashlib.new("md5", usedforsecurity=False)
        m.update(self.padded_password(self.user_password))
        m.update(bytes.fromhex(self.o))
        m.update(
            (self.access_permission & 0xFFFFFFFF).to_bytes(
                4, byteorder="little", signed=False
            )
        )
        m.update(bytes.fromhex(self.info_id))
        if self.encrypt_metadata is False and self.version == 4:
            m.update(bytes([0xFF, 0xFF, 0xFF, 0xFF]))
        result = m.digest()[: (math.ceil(self.key_length / 8))]
        for _ in range(50):
            result = md5(result)[: (math.ceil(self.key_length / 8))]
        return result


def md5(data: Union[bytes, bytearray]) -> bytes:
    h = hashlib.new("md5", usedforsecurity=False)
    h.update(data)
    return h.digest()


def int32(n: int) -> int:
    """convert long to signed 32 bit integer"""
    n = n & 0xFFFFFFFF
    return (n ^ 0x80000000) - 0x80000000
