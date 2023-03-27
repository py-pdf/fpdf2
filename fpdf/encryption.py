import hashlib
import logging
import math
from os import urandom

from .enums import EncryptionMethod
from .syntax import Name, PDFObject, PDFString
from .syntax import create_dictionary_string as pdf_dict, build_obj_dict

# try to use cryptography for AES encryption
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, modes
    from cryptography.hazmat.primitives.ciphers.algorithms import AES128
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

    def KSA(self, key):
        key_length = len(key)
        S = list(range(self.MOD))
        j = 0
        for i in range(self.MOD):
            j = (j + S[i] + key[i % key_length]) % self.MOD
            S[i], S[j] = S[j], S[i]
        return S

    def PRGA(self, S):
        i = 0
        j = 0
        while True:
            i = (i + 1) % self.MOD
            j = (j + S[i]) % self.MOD
            S[i], S[j] = S[j], S[i]
            K = S[(S[i] + S[j]) % self.MOD]
            yield K

    def encrypt(self, key, text):
        keystream = self.PRGA(self.KSA(key))
        res = []
        for c in text:
            res.append(c ^ next(keystream))
        return res


class CryptFilter:
    """Represents one crypt filter, listed under CF inside the encryption dictionary"""

    def __init__(self, mode, length):
        super().__init__()
        self.type = Name("CryptFilter")
        self.c_f_m = Name(mode)
        self.length = int(length / 8)

    def serialize(self):
        obj_dict = build_obj_dict({key: getattr(self, key) for key in dir(self)})
        return pdf_dict(obj_dict)


class EncryptionDictionary(PDFObject):
    """
    This class represents an encryption dictionary
    PDF 32000 reference - Table 20
    The PDF trailer must reference this object (/Encrypt)
    """

    def __init__(self, security_handler):
        super().__init__()
        self.filter = Name("Standard")
        self.length = security_handler.key_length
        self.r = security_handler.r
        self.o = f"<{security_handler.o.upper()}>"
        self.u = f"<{security_handler.u.upper()}>"
        self.v = security_handler.v
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
        owner_password,
        user_password=None,
        permission=None,
        encryption_method=None,
        encrypt_metadata=False,
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

        if self.encryption_method == EncryptionMethod.AES_128:
            if import_error:
                raise EnvironmentError(
                    "cryptography module not available"
                    " - Try: 'pip install cryptography' or use RC4 encryption method"
                    f" - Import error was: {import_error}"
                )
            self.v = 4
            self.r = 4
            fpdf._set_min_pdf_version("1.6")
            self.cf = CryptFilter(mode="AESV2", length=self.key_length)
        elif self.encryption_method == EncryptionMethod.NO_ENCRYPTION:
            self.v = 4
            self.r = 4
            fpdf._set_min_pdf_version("1.6")
            self.cf = CryptFilter(mode="V2", length=self.key_length)
        else:
            self.v = 2
            self.r = 3
            fpdf._set_min_pdf_version("1.5")
            # not including crypt filter because it's only required on V=4
            # if needed, it would be CryptFilter(mode=V2)

        self.encrypt_metadata = encrypt_metadata

    def generate_passwords(self, file_id):
        """Return the first hash of the PDF file id"""
        self.file_id = file_id
        self.info_id = file_id[1:33]
        self.o = self.generate_owner_password()
        self.k = self.generate_encryption_key()
        self.u = self.generate_user_password()

    def get_encryption_obj(self):
        """Return an encryption dictionary"""
        return EncryptionDictionary(self)

    def encrypt(self, text, obj_id):
        """Method invoked by PDFObject and PDFContentStream to encrypt strings and streams"""
        return (
            self.encrypt_stream(text, obj_id)
            if isinstance(text, (bytearray, bytes))
            else self.encrypt_string(text, obj_id)
        )

    def encrypt_string(self, string, obj_id):
        if self.encryption_method == EncryptionMethod.NO_ENCRYPTION:
            return PDFString(string).serialize()
        LOGGER.debug("Encrypting string: %s", string)
        return f"<{bytes(self.encrypt_bytes(string.encode('latin-1'), obj_id)).hex().upper()}>"

    def encrypt_stream(self, stream, obj_id):
        if self.encryption_method == EncryptionMethod.NO_ENCRYPTION:
            return stream
        return bytes(self.encrypt_bytes(stream, obj_id))

    def is_aes_algorithm(self):
        return self.encryption_method == EncryptionMethod.AES_128

    def encrypt_bytes(self, data, obj_id):
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

    def encrypt_AES_cryptography(self, key, data):
        iv = self.get_initialization_vector(16)
        padder = PKCS7(self.key_length).padder()
        padded_data = padder.update(data)
        padded_data += padder.finalize()
        cipher = Cipher(AES128(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        data = encryptor.update(padded_data) + encryptor.finalize()
        iv.extend(data)
        return iv

    def get_initialization_vector(self, size):
        return bytearray(urandom(size))

    def padded_password(self, password):
        """
        PDF32000 reference - Algorithm 2: Computing an encryption key
        Step (a) - Add the default padding at the end of provided password to make it 32 bit long
        """
        if len(password) > 32:
            password = password[:32]
        p = bytearray(password.encode("latin1"))
        p.extend(self.DEFAULT_PADDING[: (32 - len(p))])
        return p

    def generate_owner_password(self):
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
            result = ARC4().encrypt(new_key, result)
        return bytes(result).hex()

    def generate_user_password(self):
        """
        PDF32000 reference - Algorithm 5: Computing the encryption dictionary's U (user password) value
        The security handler is only using revision 3 or 4, so the legacy r2 version is not implemented here
        """
        m = hashlib.new("md5", usedforsecurity=False)
        m.update(bytearray(self.DEFAULT_PADDING))
        m.update(bytes.fromhex(self.info_id))
        result = m.digest()
        key = self.k
        for i in range(20):
            new_key = []
            for k in key:
                new_key.append(k ^ i)
            result = ARC4().encrypt(new_key, result)
        result.extend(
            map(lambda x: (result[x] ^ self.DEFAULT_PADDING[x]), range(16))
        )  # add 16 bytes of random padding
        return bytes(result).hex()

    def generate_encryption_key(self):
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
        if self.encrypt_metadata is False and self.v == 4:
            m.update(bytes([0xFF, 0xFF, 0xFF, 0xFF]))
        result = m.digest()[: (math.ceil(self.key_length / 8))]
        for _ in range(50):
            result = md5(result)[: (math.ceil(self.key_length / 8))]
        return result


def md5(data):
    h = hashlib.new("md5", usedforsecurity=False)
    h.update(data)
    return h.digest()


def int32(n):
    """convert long to signed 32 bit integer"""
    n = n & 0xFFFFFFFF
    return (n ^ 0x80000000) - 0x80000000
