# from fpdf import FPDF
#
# pdf = FPDF()
# pdf.add_page()
# pdf.set_font("helvetica", "B", 16)
# pdf.cell(40, 10, "Hello World!")
# pdf.output("hello1.pdf")
# pdf.encryption()
# import fpdf.encryption
# from fpdf import FPDF
#
# class PDF(fpdf.encryption):
#
#     pdf = FPDF()
#     pdf = open('tuto1.pdf')
#     pdf.output('output_filename.pdf', encryption=fpdf.encryption(owner=123, user=1234, R=4))
#     pdf.close()


# from typing import Any, Dict, NamedTuple
#
#
# class Permissions(NamedTuple):
#
#     accessibility: bool = True
#     extract: bool = True
#     modify_annotation: bool = True
#     modify_assembly: bool = False
#     modify_form: bool = True
#     modify_other: bool = True
#     print_lowres: bool = True
#     print_highres: bool = True
#
# class EncryptionInfo:
#
#     def __init__(self, encdict: Dict[str, Any]):
#         self._encdict = encdict
#
#     @property
#     def R(self) -> int:
#         return self._encdict['R']
#
#     @property
#     def V(self) -> int:
#         return self._encdict['V']
#
#     @property
#     def P(self) -> int:
#         return self._encdict['P']
#
#     @property
#     def stream_method(self) -> str:
#         return self._encdict['stream']
#
#     @property
#     def string_method(self) -> str:
#         return self._encdict['string']
#
#     @property
#     def file_method(self) -> str:
#         return self._encdict['file']
#
#     @property
#     def user_password(self) -> bytes:
#         return self._encdict['user_passwd']
#
#     @property
#     def encryption_key(self) -> bytes:
#         return self._encdict['encryption_key']
#
#     @property
#     def bits(self) -> int:
#         return len(self._encdict['encryption_key']) * 8
#
#
# class Encryption(dict):
#     def __init__(
#         self,
#         *,
#         owner: str,
#         user: str,
#         R: int = 6,
#         allow: Permissions = Permissions(),
#         aes: bool = True,
#         metadata: bool = True,
#     ):
#         super().__init__()
#         self.update(
#             dict(R=R, owner=owner, user=user, allow=allow, aes=aes, metadata=metadata)
#         )


