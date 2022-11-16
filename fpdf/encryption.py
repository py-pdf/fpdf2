import hashlib, math, os
from enum import Enum

from .syntax import Name, PDFObject, PDFString
from .syntax import create_dictionary_string as pdf_dict

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:
    Cipher = None

class EncryptionMethod(Enum):
    NO_ENCRYPTION = 1
    RC4 = 2
    AES_128 = 3


class AccessPermission():
    """
    User access permissions as defined on table 22 of the PDF spec
    Permission is an integer
    Bits 1 and 2 must be 0, positions 7, 8 and 12+ must be 1s
    Each other position signify one permission, where the value 1 enable the permission
    """
    def __init__(self, 
        print_lowres=True, 
        modify=True,
        copy=True,
        annotation=True,
        fill_forms=True,
        copy_accessibility=True,
        assemble=True,
        print_highres=True
    ):
        self.access = -3904
        if (print_lowres):
            self.access = self.access | 0b000000000100
        if (modify):
            self.access = self.access | 0b000000001000
        if (copy):    
            self.access = self.access | 0b000000010000
        if (annotation):    
            self.access = self.access | 0b000000100000
        if (fill_forms):    
            self.access = self.access | 0b000100000000
        if (copy_accessibility):    
            self.access = self.access | 0b001000000000
        if (assemble):    
            self.access = self.access | 0b010000000000
        if (print_highres):    
            self.access = self.access | 0b100000000000

    def get_permission_code(self):
        return int(self.access)

class ARC4():
    """
    This is a simplified version of the ARC4 (alleged RC4) algorithm, created based on the following sources:
    * Wikipedia article on RC4
    * github.com/manojpandey/rc4 (MIT License)
    * http://people.csail.mit.edu/rivest/pubs/RS14.pdf

    Having this ARC4 implementation makes it possible to have basic encryption functions without additional dependencies
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
    """ Represents one crypt filter, listed under CF inside the encryption dictionary """
    def __init__(self, mode):
        super().__init__()
        self.type = Name("CryptFilter")
        self.c_f_m = Name(mode)

    def serialize(self):
        self.id = 0   # avoid build_obj_dict error
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
        self.o = f'<{security_handler.o}>'
        self.u = f'<{security_handler.u}>'
        self.v = security_handler.v
        self.p = security_handler.access_permission.get_permission_code()
        if (security_handler.encrypt_metadata == False):
            self.encrypt_metadata = "false"
        if (security_handler.cf):
            self.c_f = pdf_dict({'/StdCF' : security_handler.cf.serialize()})
        if (security_handler.encryption_method == EncryptionMethod.NO_ENCRYPTION):
            self.stm_f = Name("Identity")  # crypt filter for streams
            self.str_f = Name("Identity")  # crypt filter for strings
        else:
            self.stm_f = Name("StdCF")  # crypt filter for streams
            self.str_f = Name("StdCF")  # crypt filter for strings
        
        
class StandardSecurityHandler():
    """
    This class is reference on the main PDF class and is used to handle all encryption functions
        * Calculate password and hashes
        * Provide encrypt method to be called by stream and strings
        * Set the access permissions on the document
    """

    DEFAULT_PADDING = [0x28, 0xBF, 0x4E, 0x5E, 0x4E, 0x75, 0x8A, 0x41,
                       0x64, 0x00, 0x4E, 0x56, 0xFF, 0xFA, 0x01, 0x08,
                       0x2E, 0x2E, 0x00, 0xB6, 0xD0, 0x68, 0x3E, 0x80,
                       0x2F, 0x0C, 0xA9, 0xFE, 0x64, 0x53, 0x69, 0x7A]

    def __init__(self,
                fpdf,
                owner_password,
                user_password=None,
                access_permission=None,
                encryption_method=None,
                encrypt_metadata=False
        ):
        
        self.info_id = fpdf.file_id()[1:33]
        self.access_permission = access_permission
        self.owner_password = owner_password
        self.user_password = user_password if (user_password) else ''
        self.encryption_method = encryption_method if (encryption_method) else EncryptionMethod.RC4
        self.cf = None

        if (self.encryption_method == EncryptionMethod.AES_128):
            if (Cipher == None):
                raise EnvironmentError(
                "cryptography not available - Try: 'pip install cryptography' or use another encryption method"
            )
            self.v = 4
            self.r = 4
            self.key_length = 128
            fpdf._set_min_pdf_version("1.6")
            self.cf = CryptFilter(mode="AESV2")
        elif (self.encryption_method == EncryptionMethod.NO_ENCRYPTION):
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
        """ Return an encryption dictionary """
        return EncryptionDictionary(self)

    def encrypt(self, text, obj_id):
        """ Method invoked by PDFObject and PDFContentStream to encrype strings and streams """
        if isinstance(text, (bytearray, bytes)):
            return text if (self.encryption_method == EncryptionMethod.NO_ENCRYPTION) else bytes(self.encrypt_bytes(text, obj_id))
        else:
            if (self.encryption_method == EncryptionMethod.NO_ENCRYPTION):
                return PDFString(text).serialize() 
            else: 
                return f"<{bytes(self.encrypt_bytes(text.encode('latin-1'), obj_id)).hex()}>"

    def aes_algorithm(self):
        return (self.encryption_method == EncryptionMethod.AES_128)

    def encrypt_bytes(self, input, obj_id):
        """
        PDF32000 reference - Algorithm 1: Encryption of data using the RC4 or AES algorithms
        Append object ID and generation ID to the key and encrypt the data
        Generation ID is fixed as 0. Will need to revisit if the application start changing generation ID
        """
        h = hashlib.md5(self.k)
        h.update((obj_id & 0xffffff).to_bytes(3, byteorder = 'little', signed=False)) # object id
        h.update((0 & 0xffff).to_bytes(2, byteorder = 'little', signed=False))        # generation id
        if (self.aes_algorithm()):
            h.update(bytes([0x73, 0x41, 0x6c, 0x54]))                                 # add salt (sAlT) for AES
        key = h.digest()
        if (((self.key_length / 8) + 5 ) < 16):
            key = key[:((self.key_length / 8) + 5 )]

        if (self.aes_algorithm()):
            iv = bytearray(os.urandom(16))
            input = bytearray(input)
            for i in range (16 - (len(input) % 16)):
                input.extend(bytes([0x00]))
            cipher = Cipher(algorithms.AES128(key), modes.CBC(iv))
            e = cipher.encryptor()
            data = e.update(input) + e.finalize()
            iv.extend(data)
            return iv
        else:
            return ARC4().encrypt(key, input)

    def padded_password(self, password):
        """
        PDF32000 reference - Algorithm 2: Computing an encryption key
        Step (a) - Add the default padding at the end of provided password to make it 32 bit long
        """
        if len(password) > 32:
            password = password[:32]
        p = bytearray(password.encode('latin1'))
        p.extend(self.DEFAULT_PADDING[:(32 - len(p))])
        return p

    def generate_owner_password(self):
        """ 
        PDF32000 reference - Algorithm 3: Computing the encryption dictionary's O (owner password) value 
        The security handler is only using revision 3 or 4, so the legacy r2 version is not implemented here
        """
        m = self.padded_password(self.owner_password)
        for i in range(51):
            m = hashlib.md5(m).digest()
        rc4key = m[:(math.ceil(self.key_length / 8))]
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
        result.extend(map(lambda x: (result[x] ^ self.DEFAULT_PADDING[x]), range(16))) # add 16 bytes of random padding
        return bytes(result).hex()
    
    #def generate_r2_user_password(self, user_password):
    #    u = RC4().encrypt(self.padded_password(user_password), self.DEFAULT_PADDING)
    #    return bytes(u).hex()

    def generate_encryption_key(self):
        """
        PDF32000 reference
        Algorithm 2: Computing an encryption key
        """
        m = hashlib.md5(self.padded_password(self.user_password))
        m.update(bytes.fromhex(self.o))
        m.update((self.access_permission.get_permission_code() & 0xffffffff).to_bytes(4, byteorder = 'little', signed=False))
        m.update(bytes.fromhex(self.info_id))
        if (self.encrypt_metadata == False and self.v == 4):
            m.update(bytes([0xff, 0xff, 0xff, 0xff]))
        result = m.digest()[:(math.ceil(self.key_length / 8))]
        for i in range(50):
             m = hashlib.md5(result)
             result = m.digest()[:(math.ceil(self.key_length / 8))]
        return result
