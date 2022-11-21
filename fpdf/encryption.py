import hashlib
import math
from os import urandom

from .enums import EncryptionMethod
from .syntax import Name, PDFObject, PDFString
from .syntax import create_dictionary_string as pdf_dict

# try to use cryptography for AES encryption
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    crypto = "cryptography"
except ImportError:
    crypto = None

# If cryptography is not present, try Crypto
if not crypto:
    try:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad

        crypto = "crypto"
    except ImportError:
        crypto = None


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


class CryptFilter(PDFObject):
    """Represents one crypt filter, listed under CF inside the encryption dictionary"""

    def __init__(self, mode):
        super().__init__()
        self.type = Name("CryptFilter")
        self.c_f_m = Name(mode)

    def serialize(self, obj_dict=None, encryption_handler=None):
        self.id = 0  # avoid build_obj_dict error
        output = []
        output.append("<<")
        obj_dict = self._build_obj_dict()
        output.append(pdf_dict(obj_dict, open_dict="", close_dict=""))
        output.append(">>")
        return "\n".join(output)


class EncryptionDictionary(PDFObject):
    """
    This class represents an encryption dictionary
    PDF 32000 reference - Table 20
    The PDF trailer must reference this object (/Encrypt)
    """

    def __init__(self, security_handler):
        super().__init__()
        self.filter = Name("Standard")
        self.length = 128
        self.r = security_handler.r
        self.o = f"<{security_handler.o}>"
        self.u = f"<{security_handler.u}>"
        self.v = security_handler.v
        self.p = security_handler.access_permission
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
    This class is reference on the main PDF class and is used to handle all encryption functions
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

        self.info_id = fpdf.file_id()[1:33]
        self.access_permission = -3904 if (permission is None) else (-3904 | permission)
        self.owner_password = owner_password
        self.user_password = user_password if (user_password) else ""
        self.encryption_method = (
            encryption_method if (encryption_method) else EncryptionMethod.RC4
        )
        self.cf = None

        if self.encryption_method == EncryptionMethod.AES_128:
            if crypto is None:
                raise EnvironmentError(
                    "cryptography not available - Try: 'pip install cryptography' or use another encryption method"
                )
            self.v = 4
            self.r = 4
            self.key_length = 128
            fpdf._set_min_pdf_version("1.6")
            self.cf = CryptFilter(mode="AESV2")
        elif self.encryption_method == EncryptionMethod.NO_ENCRYPTION:
            self.v = 4
            self.r = 4
            self.key_length = 128
            fpdf._set_min_pdf_version("1.6")
            self.cf = CryptFilter(mode="V2")
        else:
            self.v = 2
            self.r = 3
            self.key_length = 128
            fpdf._set_min_pdf_version("1.4")
            # not including crypt filter because it's only required on V=4
            # if needed, it would be CryptFilter(mode=V2)

        self.encrypt_metadata = encrypt_metadata
        self.o = self.generate_owner_password()
        self.k = self.generate_encryption_key()
        self.u = self.generate_user_password()

    def get_encryption_obj(self):
        """Return an encryption dictionary"""
        return EncryptionDictionary(self)

    def encrypt(self, text, obj_id):
        """Method invoked by PDFObject and PDFContentStream to encrype strings and streams"""
        return (
            self.encrypt_stream(text, obj_id)
            if isinstance(text, (bytearray, bytes))
            else self.encrypt_string(text, obj_id)
        )

    def encrypt_string(self, string, obj_id):
        if self.encryption_method == EncryptionMethod.NO_ENCRYPTION:
            return PDFString(string).serialize()
        return f"<{bytes(self.encrypt_bytes(string.encode('latin-1'), obj_id)).hex()}>"

    def encrypt_stream(self, stream, obj_id):
        if self.encryption_method == EncryptionMethod.NO_ENCRYPTION:
            return stream
        return bytes(self.encrypt_bytes(stream, obj_id))

    def aes_algorithm(self):
        return self.encryption_method == EncryptionMethod.AES_128

    def encrypt_bytes(self, data, obj_id):
        """
        PDF32000 reference - Algorithm 1: Encryption of data using the RC4 or AES algorithms
        Append object ID and generation ID to the key and encrypt the data
        Generation ID is fixed as 0. Will need to revisit if the application start changing generation ID
        """
        h = hashlib.md5(self.k)
        h.update(
            (obj_id & 0xFFFFFF).to_bytes(3, byteorder="little", signed=False)
        )  # object id
        h.update(
            (0 & 0xFFFF).to_bytes(2, byteorder="little", signed=False)
        )  # generation id
        if self.aes_algorithm():
            h.update(bytes([0x73, 0x41, 0x6C, 0x54]))  # add salt (sAlT) for AES
        key = h.digest()
        if ((self.key_length / 8) + 5) < 16:
            key = key[: ((self.key_length / 8) + 5)]

        if self.aes_algorithm():
            return (
                self.encrypt_AES_cryptography(key, data)
                if crypto == "cryptography"
                else self.encrypt_AES_crypto(key, data)
            )
        return ARC4().encrypt(key, data)

    def encrypt_AES_cryptography(self, key, data):
        iv = bytearray(urandom(16))
        b = bytearray(data)
        for _ in range(16 - (len(b) % 16)):
            b.extend(bytes([0x00]))
        cipher = Cipher(algorithms.AES128(key), modes.CBC(iv))
        e = cipher.encryptor()
        data = e.update(b) + e.finalize()
        iv.extend(data)
        return iv

    def encrypt_AES_crypto(self, key, data):
        cipher = AES.new(key, AES.MODE_CBC)
        result = cipher.encrypt(pad(data, AES.block_size))
        r = bytearray(cipher.iv)
        r.extend(result)
        return r

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
            m = hashlib.md5(m).digest()
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
        m = hashlib.md5(bytearray(self.DEFAULT_PADDING))
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
        m = hashlib.md5(self.padded_password(self.user_password))
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
            m = hashlib.md5(result)
            result = m.digest()[: (math.ceil(self.key_length / 8))]
        return result
