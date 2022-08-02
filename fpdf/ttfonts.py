# ******************************************************************************
# TTFontFile class
#
# This class is based on The ReportLab Open Source PDF library
# written in Python - http://www.reportlab.com/software/opensource/
# together with ideas from the OpenOffice source code and others.
#
# Version:  1.04
# Date:     2011-09-18
# Author:   Ian Back <ianb@bpm1.com>
# License:  LGPL
# Copyright (c) Ian Back, 2010
# Ported to Python 2.7 by Mariano Reingart (reingart@gmail.com) on 2012
# This header must be retained in any redistribution or
# modification of the file.
#
# ******************************************************************************

import re
import warnings
from struct import error as StructError, pack, unpack

from .util import b, substr

# Define the value used in the "head" table of a created TTF file
# 0x74727565 "true" for Mac
# 0x00010000 for Windows
# Either seems to work for a font embedded in a PDF file
# when read by Adobe Reader on a Windows PC(!)
_TTF_MAC_HEADER = False

# TrueType Font Glyph operators
GF_WORDS = 1 << 0
GF_SCALE = 1 << 3
GF_MORE = 1 << 5
GF_XYSCALE = 1 << 6
GF_TWOBYTWO = 1 << 7


def sub32(x, y):
    xlo = x[1]
    xhi = x[0]
    ylo = y[1]
    yhi = y[0]
    if ylo > xlo:
        xlo += 1 << 16
        yhi += 1
    reslo = xlo - ylo
    if yhi > xhi:
        xhi += 1 << 16
    reshi = xhi - yhi
    reshi = reshi & 0xFFFF
    return reshi, reslo


def calcChecksum(data):
    if len(data) % 4:
        data += b("\0") * (4 - (len(data) % 4))
    hi = 0x0000
    lo = 0x0000
    for i in range(0, len(data), 4):
        hi += (data[i] << 8) + data[i + 1]
        lo += (data[i + 2] << 8) + data[i + 3]
        hi += lo >> 16
        lo &= 0xFFFF
        hi &= 0xFFFF
    return hi, lo


class TTFontFile:
    def __init__(self):
        # Maximum size of glyph table to read in as string
        # (otherwise reads each glyph from file)
        self.maxStrLenRead = 200000

    def getMetrics(self, file):
        self.filename = file
        with open(file, "rb") as self.fh:
            self._pos = 0
            self.charWidths = []
            self.glyphPos = {}
            self.charToGlyph = {}
            self.tables = {}
            self.otables = {}
            self.ascent = 0
            self.descent = 0
            self.version = version = self.read_ulong()
            if version == 0x4F54544F:
                raise RuntimeError("Postscript outlines are not supported")
            if version == 0x74746366:
                raise RuntimeError("ERROR - TrueType Fonts Collections not supported")
            if version not in (0x00010000, 0x74727565):
                raise RuntimeError(f"Not a TrueType font: version=0x{version:x}")
            self.readTableDirectory()
            self.extractInfo()

    def readTableDirectory(
        self,
    ):
        self.numTables = self.read_ushort()
        self.searchRange = self.read_ushort()
        self.entrySelector = self.read_ushort()
        self.rangeShift = self.read_ushort()
        self.tables = {}
        for _ in range(self.numTables):
            record = {
                "tag": self.read_tag(),
                "checksum": (self.read_ushort(), self.read_ushort()),
                "offset": self.read_ulong(),
                "length": self.read_ulong(),
            }
            self.tables[record["tag"]] = record

    def get_table_pos(self, tag):
        offset = self.tables[tag]["offset"]
        length = self.tables[tag]["length"]
        return offset, length

    def seek(self, pos):
        self._pos = pos
        self.fh.seek(self._pos)

    def skip(self, delta):
        self._pos = self._pos + delta
        self.fh.seek(self._pos)

    def seek_table(self, tag, offset_in_table=0):
        tpos = self.get_table_pos(tag)
        self._pos = tpos[0] + offset_in_table
        self.fh.seek(self._pos)
        return self._pos

    def read_tag(self):
        self._pos += 4
        return self.fh.read(4).decode("latin1")

    def read_short(self):
        self._pos += 2
        s = self.fh.read(2)
        a = (s[0] << 8) + s[1]
        if a & (1 << 15):
            a = a - (1 << 16)
        return a

    def read_ushort(self):
        self._pos += 2
        s = self.fh.read(2)
        return (s[0] << 8) + s[1]

    def read_ulong(self):
        self._pos += 4
        s = self.fh.read(4)
        # if large uInt32 as an integer, PHP converts it to -ve
        return s[0] * 16777216 + (s[1] << 16) + (s[2] << 8) + s[3]  # 16777216  = 1<<24

    def get_ushort(self, pos):
        self.fh.seek(pos)
        s = self.fh.read(2)
        return (s[0] << 8) + s[1]

    @staticmethod
    def splice(stream, offset, value):
        return substr(stream, 0, offset) + value + substr(stream, offset + len(value))

    def _set_ushort(self, stream, offset, value):
        up = pack(">H", value)
        return self.splice(stream, offset, up)

    def get_chunk(self, pos, length):
        self.fh.seek(pos)
        if length < 1:
            return ""
        return self.fh.read(length)

    def get_table(self, tag):
        (pos, length) = self.get_table_pos(tag)
        if length == 0:
            raise RuntimeError(
                f"Truetype font ({self.filename}): error reading table: {tag}"
            )
        self.fh.seek(pos)
        return self.fh.read(length)

    def add(self, tag, data):
        if tag == "head":
            data = self.splice(data, 8, b("\0\0\0\0"))
        self.otables[tag] = data

    def extractInfo(self):
        # name - Naming table
        self.sFamilyClass = 0
        self.sFamilySubClass = 0

        name_offset = self.seek_table("name")
        fmt = self.read_ushort()
        if fmt != 0:
            raise RuntimeError(f"Unknown name table format {fmt}")
        numRecords = self.read_ushort()
        string_data_offset = name_offset + self.read_ushort()
        names = {1: "", 2: "", 3: "", 4: "", 6: ""}
        K = list(names)
        nameCount = len(names)
        for _ in range(numRecords):
            platformId = self.read_ushort()
            encodingId = self.read_ushort()
            languageId = self.read_ushort()
            nameId = self.read_ushort()
            length = self.read_ushort()
            offset = self.read_ushort()
            if nameId not in K:
                continue
            N = ""
            if (
                platformId == 3 and encodingId == 1 and languageId == 0x409
            ):  # Microsoft, Unicode, US English, PS Name
                opos = self._pos
                self.seek(string_data_offset + offset)
                if length % 2 != 0:
                    raise RuntimeError(
                        "PostScript name is UTF-16BE string of odd length"
                    )
                length //= 2
                N = ""
                while length > 0:
                    char = self.read_ushort()
                    N += chr(char)
                    length -= 1
                self._pos = opos
                self.seek(opos)

            elif (
                platformId == 1 and encodingId == 0 and languageId == 0
            ):  # Macintosh, Roman, English, PS Name
                opos = self._pos
                N = self.get_chunk(string_data_offset + offset, length).decode("latin1")
                self._pos = opos
                self.seek(opos)

            if N and names[nameId] == "":
                names[nameId] = N
                nameCount -= 1
                if nameCount == 0:
                    break

        if names[6]:
            psName = names[6]
        elif names[4]:
            psName = re.sub(" ", "-", names[4])
        elif names[1]:
            psName = re.sub(" ", "-", names[1])
        else:
            psName = ""
        if not psName:
            raise RuntimeError("Could not find PostScript font name")
        self.name = psName
        self.familyName = names[1] or psName
        self.styleName = names[2] or "Regular"
        self.fullName = names[4] or psName
        self.uniqueFontID = names[3] or psName
        if names[6]:
            self.fullName = names[6]

        # head - Font header table
        self.seek_table("head")
        self.skip(18)
        self.unitsPerEm = unitsPerEm = self.read_ushort()
        scale = 1000 / unitsPerEm
        self.skip(16)
        xMin = self.read_short()
        yMin = self.read_short()
        xMax = self.read_short()
        yMax = self.read_short()
        self.bbox = [(xMin * scale), (yMin * scale), (xMax * scale), (yMax * scale)]
        self.skip(3 * 2)
        # pylint: disable=unused-variable
        indexToLocFormat = self.read_ushort()
        glyphDataFormat = self.read_ushort()
        if glyphDataFormat != 0:
            raise RuntimeError(f"Unknown glyph data format {glyphDataFormat}")

        # hhea metrics table
        # ttf2t1 seems to use this value rather than the one in OS/2 - so put in for
        # compatibility
        if "hhea" in self.tables:
            self.seek_table("hhea")
            self.skip(4)
            hheaAscender = self.read_short()
            hheaDescender = self.read_short()
            self.ascent = hheaAscender * scale
            self.descent = hheaDescender * scale

        # OS/2 - OS/2 and Windows metrics table
        if "OS/2" in self.tables:
            self.seek_table("OS/2")
            version = self.read_ushort()
            self.skip(2)
            usWeightClass = self.read_ushort()
            self.skip(2)
            fsType = self.read_ushort()
            if fsType == 0x0002 or (fsType & 0x0300) != 0:
                raise RuntimeError(
                    f"ERROR - Font file {self.filename} cannot be embedded due to copyright restrictions."
                )

            self.skip(20)
            sF = self.read_short()
            self.sFamilyClass = sF >> 8
            self.sFamilySubClass = sF & 0xFF
            self._pos += 10  # PANOSE = 10 byte length
            panose = self.fh.read(10)
            self.skip(26)
            sTypoAscender = self.read_short()
            sTypoDescender = self.read_short()
            if not self.ascent:
                self.ascent = sTypoAscender * scale
            if not self.descent:
                self.descent = sTypoDescender * scale
            if version > 1:
                self.skip(16)
                sCapHeight = self.read_short()
                self.capHeight = sCapHeight * scale
            else:
                self.capHeight = self.ascent

        else:
            usWeightClass = 500
            if not self.ascent:
                self.ascent = yMax * scale
            if not self.descent:
                self.descent = yMin * scale
            self.capHeight = self.ascent

        self.stemV = 50 + int(pow((usWeightClass / 65), 2))

        # post - PostScript table
        self.seek_table("post")
        self.skip(4)
        self.italicAngle = self.read_short() + self.read_ushort() / 65536
        self.underlinePosition = self.read_short() * scale
        self.underlineThickness = self.read_short() * scale
        isFixedPitch = self.read_ulong()

        self.flags = 4

        if self.italicAngle != 0:
            self.flags |= 64
        if usWeightClass >= 600:
            self.flags |= 262144
        if isFixedPitch:
            self.flags |= 1

        # hhea - Horizontal header table
        self.seek_table("hhea")
        self.skip(32)
        metricDataFormat = self.read_ushort()
        if metricDataFormat != 0:
            raise RuntimeError(
                f"Unknown horizontal metric data format: {metricDataFormat}"
            )
        numberOfHMetrics = self.read_ushort()
        if numberOfHMetrics == 0:
            raise RuntimeError("Number of horizontal metrics is 0")

        # maxp - Maximum profile table
        self.seek_table("maxp")
        self.skip(4)
        numGlyphs = self.read_ushort()

        # cmap - Character to glyph index mapping table
        cmap_offset = self.seek_table("cmap")
        self.skip(2)
        cmapTableCount = self.read_ushort()
        unicode_cmap_offset = 0
        unicode_cmap_offset12 = 0

        for _ in range(cmapTableCount):
            platformID = self.read_ushort()
            encodingID = self.read_ushort()
            offset = self.read_ulong()
            save_pos = self._pos
            if platformID == 3 and encodingID == 10:  # Microsoft, UCS-4
                fmt = self.get_ushort(cmap_offset + offset)
                if fmt == 12:
                    if not unicode_cmap_offset12:
                        unicode_cmap_offset12 = cmap_offset + offset
                    break
            if (
                platformID == 3 and encodingID == 1
            ) or platformID == 0:  # Microsoft, Unicode
                fmt = self.get_ushort(cmap_offset + offset)
                if fmt == 4:
                    if not unicode_cmap_offset:
                        unicode_cmap_offset = cmap_offset + offset
                    # Don't break here since we might later get
                    # unicode_cmap_offset12 which is needed for
                    # characters => 0x10000 (CMAP12)
                    #
                    # break

            self.seek(save_pos)

        if not unicode_cmap_offset and not unicode_cmap_offset12:
            raise RuntimeError(
                f"Font ({self.filename}) does not have cmap for Unicode (platform 3, "
                f"encoding 1, format 4, or platform 3, encoding 10, format 12, or "
                f"platform 0, any encoding, format 4)"
            )

        glyphToChar = {}
        charToGlyph = {}
        if unicode_cmap_offset12:
            self.getCMAP12(unicode_cmap_offset12, glyphToChar, charToGlyph)
        else:
            self.getCMAP4(unicode_cmap_offset, glyphToChar, charToGlyph)

        # hmtx - Horizontal metrics table
        self.getHMTX(numberOfHMetrics, numGlyphs, glyphToChar, scale)

    def makeSubset(self, file, subset):
        self.filename = file
        with open(file, "rb") as self.fh:
            self._pos = 0
            self.charWidths = []
            self.glyphPos = {}
            self.charToGlyph = {}
            self.tables = {}
            self.otables = {}
            self.ascent = 0
            self.descent = 0
            self.skip(4)
            self.maxUni = 0
            self.readTableDirectory()

            # head - Font header table
            self.seek_table("head")
            self.skip(50)
            indexToLocFormat = self.read_ushort()
            # pylint: disable=unused-variable
            glyphDataFormat = self.read_ushort()

            # hhea - Horizontal header table
            self.seek_table("hhea")
            self.skip(32)
            metricDataFormat = self.read_ushort()
            orignHmetrics = numberOfHMetrics = self.read_ushort()

            # maxp - Maximum profile table
            self.seek_table("maxp")
            self.skip(4)
            numGlyphs = self.read_ushort()

            # cmap - Character to glyph index mapping table
            cmap_offset = self.seek_table("cmap")
            self.skip(2)
            cmapTableCount = self.read_ushort()
            unicode_cmap_offset = 0
            unicode_cmap_offset12 = 0
            for _ in range(cmapTableCount):
                platformID = self.read_ushort()
                encodingID = self.read_ushort()
                offset = self.read_ulong()
                save_pos = self._pos
                if platformID == 3 and encodingID == 10:  # Microsoft, UCS-4
                    fmt = self.get_ushort(cmap_offset + offset)
                    if fmt == 12:
                        if not unicode_cmap_offset12:
                            unicode_cmap_offset12 = cmap_offset + offset
                        break
                if (
                    platformID == 3 and encodingID == 1
                ) or platformID == 0:  # Microsoft, Unicode
                    fmt = self.get_ushort(cmap_offset + offset)
                    if fmt == 4:
                        unicode_cmap_offset = cmap_offset + offset
                        # Don't break here since we might later get
                        # unicode_cmap_offset12 which is needed for
                        # characters => 0x10000 (CMAP12)
                        #
                        # break

                self.seek(save_pos)

            if not unicode_cmap_offset and not unicode_cmap_offset12:
                raise RuntimeError(
                    f"Font ({self.filename}) does not have cmap for Unicode "
                    f"(platform 3, encoding 1, format 4, or platform 3, encoding 10, "
                    f"format 12, or platform 0, any encoding, format 4)"
                )

            glyphToChar = {}
            charToGlyph = {}
            if unicode_cmap_offset12:
                self.getCMAP12(unicode_cmap_offset12, glyphToChar, charToGlyph)
            else:
                self.getCMAP4(unicode_cmap_offset, glyphToChar, charToGlyph)

            self.charToGlyph = charToGlyph

            # hmtx - Horizontal metrics table
            scale = 1  # not used
            self.getHMTX(numberOfHMetrics, numGlyphs, glyphToChar, scale)

            # loca - Index to location
            self.getLOCA(indexToLocFormat, numGlyphs)

            subsetglyphs = [(0, 0)]  # special "sorted dict"!
            subsetCharToGlyph = {}
            for code in subset:
                target = subset[code] if isinstance(subset, dict) else code
                if target > 65535:
                    raise Exception(
                        f"Character U+{target:X} must be remapped since it cannot be indexed in CMAP4 table"
                    )
                if code in self.charToGlyph:
                    if (self.charToGlyph[code], target) not in subsetglyphs:
                        subsetglyphs.append(
                            (self.charToGlyph[code], target)
                        )  # Old Glyph ID => Unicode
                    subsetCharToGlyph[target] = self.charToGlyph[
                        code
                    ]  # Unicode to old GlyphID
                self.maxUni = max(self.maxUni, code)
            (start, _) = self.get_table_pos("glyf")

            subsetglyphs.sort()
            glyphSet = {}
            n = 0
            # maximum Unicode index (character code) in this font, according to the cmap
            # subtable for platform ID 3 and platform- specific encoding ID 0 or 1.
            fsLastCharIndex = 0
            for originalGlyphIdx, uni in subsetglyphs:
                fsLastCharIndex = max(fsLastCharIndex, uni)
                glyphSet[originalGlyphIdx] = n  # old glyphID to new glyphID
                n += 1

            codeToGlyph = {}
            for uni, originalGlyphIdx in sorted(subsetCharToGlyph.items()):
                codeToGlyph[uni] = glyphSet[originalGlyphIdx]

            self.codeToGlyph = codeToGlyph

            for originalGlyphIdx, uni in subsetglyphs:
                nonlocals = {
                    "start": start,
                    "glyphSet": glyphSet,
                    "subsetglyphs": subsetglyphs,
                }
                self.getGlyphs(originalGlyphIdx, nonlocals)

            numGlyphs = numberOfHMetrics = len(subsetglyphs)

            # tables copied from the original
            tags = ["name"]
            for tag in tags:
                self.add(tag, self.get_table(tag))
            tags = ["cvt ", "fpgm", "prep", "gasp"]
            for tag in tags:
                if tag in self.tables:
                    self.add(tag, self.get_table(tag))

            # post - PostScript
            opost = self.get_table("post")
            post = (
                b("\x00\x03\x00\x00")
                + substr(opost, 4, 12)
                + b("\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
            )
            self.add("post", post)

            # Sort CID2GID map into segments of contiguous codes
            if 0 in codeToGlyph:
                del codeToGlyph[0]
            # unset(codeToGlyph[65535])
            rangeid = 0
            range_ = {}
            prevcid = -2
            prevglidx = -1
            # for each character
            for cid, glidx in sorted(codeToGlyph.items()):
                if cid == (prevcid + 1) and glidx == (prevglidx + 1):
                    range_[rangeid].append(glidx)
                else:
                    # new range
                    rangeid = cid
                    range_[rangeid] = []
                    range_[rangeid].append(glidx)
                prevcid = cid
                prevglidx = glidx

            # cmap - Character to glyph mapping - Format 4 (MS / )
            segCount = len(range_) + 1  # + 1 Last segment has missing character 0xFFFF
            searchRange = 1
            entrySelector = 0
            while searchRange * 2 <= segCount:
                searchRange = searchRange * 2
                entrySelector = entrySelector + 1

            searchRange = searchRange * 2
            rangeShift = segCount * 2 - searchRange
            length = 16 + (8 * segCount) + (numGlyphs + 1)
            cmap = [
                0,
                1,  # Index : version, number of encoding subtables
                3,
                1,  # Encoding Subtable : platform (MS=3), encoding (Unicode)
                0,
                12,  # Encoding Subtable : offset (hi,lo)
                4,
                length,
                0,  # Format 4 Mapping subtable: format, length, language
                segCount * 2,
                searchRange,
                entrySelector,
                rangeShift,
            ]

            range_ = sorted(range_.items())

            # endCode(s)
            for start, subrange in range_:
                endCode = start + (len(subrange) - 1)
                cmap.append(endCode)  # endCode(s)

            cmap.append(0xFFFF)  # endCode of last Segment
            cmap.append(0)  # reservedPad

            # startCode(s)
            for start, subrange in range_:
                cmap.append(start)  # startCode(s)

            cmap.append(0xFFFF)  # startCode of last Segment
            # idDelta(s)
            for start, subrange in range_:
                idDelta = -(start - subrange[0])
                n += len(subrange)
                cmap.append(idDelta)  # idDelta(s)

            cmap.append(1)  # idDelta of last Segment
            # idRangeOffset(s)
            for subrange in range_:
                # idRangeOffset[segCount]   Offset in bytes to glyph indexArray, or 0
                cmap.append(0)

            cmap.append(0)  # idRangeOffset of last Segment
            for subrange, glidx in range_:
                cmap.extend(glidx)

            cmap.append(0)  # Mapping for last character
            cmapstr = b("")
            for cm in cmap:
                if cm >= 0:
                    cmapstr += pack(">H", cm)
                else:
                    try:
                        cmapstr += pack(">h", cm)
                    except StructError:
                        # cmap value too big to fit in a short (h),
                        # putting it in an unsigned short (H):
                        cmapstr += pack(">H", -cm)
            self.add("cmap", cmapstr)

            # glyf - Glyph data
            (glyfOffset, glyfLength) = self.get_table_pos("glyf")
            if glyfLength < self.maxStrLenRead:
                glyphData = self.get_table("glyf")

            offsets = []
            glyf = b("")
            pos = 0

            hmtxstr = b("")
            maxComponentElements = 0  # number of glyphs referenced at top level
            self.glyphdata = {}

            for originalGlyphIdx, uni in subsetglyphs:
                # hmtx - Horizontal Metrics
                hm = self.getHMetric(orignHmetrics, originalGlyphIdx)
                hmtxstr += hm

                offsets.append(pos)
                try:
                    glyphPos = self.glyphPos[originalGlyphIdx]
                    glyphLen = self.glyphPos[originalGlyphIdx + 1] - glyphPos
                except IndexError:
                    warnings.warn(f"Missing glyph {originalGlyphIdx} in {file}")
                    glyphLen = 0

                if glyfLength < self.maxStrLenRead:
                    data = substr(glyphData, glyphPos, glyphLen)
                else:
                    if glyphLen > 0:
                        data = self.get_chunk(glyfOffset + glyphPos, glyphLen)
                    else:
                        data = b("")

                if glyphLen > 0:
                    up = unpack(">H", substr(data, 0, 2))[0]
                if glyphLen > 2 and (
                    up & (1 << 15)
                ):  # If number of contours <= -1 i.e. composite glyph
                    pos_in_glyph = 10
                    flags = GF_MORE
                    nComponentElements = 0
                    while flags & GF_MORE:
                        nComponentElements += (
                            1  # number of glyphs referenced at top level
                        )
                        up = unpack(">H", substr(data, pos_in_glyph, 2))
                        flags = up[0]
                        up = unpack(">H", substr(data, pos_in_glyph + 2, 2))
                        glyphIdx = up[0]
                        self.glyphdata.setdefault(originalGlyphIdx, {}).setdefault(
                            "compGlyphs", []
                        ).append(glyphIdx)
                        try:
                            data = self._set_ushort(
                                data, pos_in_glyph + 2, glyphSet[glyphIdx]
                            )
                        except KeyError:
                            data = 0
                            warnings.warn(f"Missing glyph data {glyphIdx} in {file}")
                        pos_in_glyph += 4
                        if flags & GF_WORDS:
                            pos_in_glyph += 4
                        else:
                            pos_in_glyph += 2
                        if flags & GF_SCALE:
                            pos_in_glyph += 2
                        elif flags & GF_XYSCALE:
                            pos_in_glyph += 4
                        elif flags & GF_TWOBYTWO:
                            pos_in_glyph += 8

                    maxComponentElements = max(maxComponentElements, nComponentElements)

                glyf += data
                pos += glyphLen
                if pos % 4 != 0:
                    padding = 4 - (pos % 4)
                    glyf += b("\0") * padding
                    pos += padding

            offsets.append(pos)
            self.add("glyf", glyf)

            # hmtx - Horizontal Metrics
            self.add("hmtx", hmtxstr)

            # loca - Index to location
            locastr = b("")
            if ((pos + 1) >> 1) > 0xFFFF:
                indexToLocFormat = 1  # long format
                for offset in offsets:
                    locastr += pack(">L", offset)
            else:
                indexToLocFormat = 0  # short format
                for offset in offsets:
                    locastr += pack(">H", offset // 2)

            self.add("loca", locastr)

            # head - Font header
            head = self.get_table("head")
            head = self._set_ushort(head, 50, indexToLocFormat)
            self.add("head", head)

            # hhea - Horizontal Header
            hhea = self.get_table("hhea")
            hhea = self._set_ushort(hhea, 34, numberOfHMetrics)
            self.add("hhea", hhea)

            # maxp - Maximum Profile
            maxp = self.get_table("maxp")
            maxp = self._set_ushort(maxp, 4, numGlyphs)
            self.add("maxp", maxp)

            # OS/2 - OS/2
            os2 = self.get_table("OS/2")
            self.add("OS/2", os2)

        # Put the TTF file together
        stm = self.endTTFile("")
        return stm

    # Recursively get composite glyphs
    def getGlyphs(self, originalGlyphIdx, nonlocals):
        # &start, &glyphSet, &subsetglyphs)

        try:
            glyphPos = self.glyphPos[originalGlyphIdx]
            glyphLen = self.glyphPos[originalGlyphIdx + 1] - glyphPos
        except IndexError:
            return

        if not glyphLen:
            return

        self.seek(nonlocals["start"] + glyphPos)
        numberOfContours = self.read_short()
        if numberOfContours < 0:
            self.skip(8)
            flags = GF_MORE
            while flags & GF_MORE:
                flags = self.read_ushort()
                glyphIdx = self.read_ushort()
                if glyphIdx not in nonlocals["glyphSet"]:
                    nonlocals["glyphSet"][glyphIdx] = len(
                        nonlocals["subsetglyphs"]
                    )  # old glyphID to new glyphID
                    nonlocals["subsetglyphs"].append((glyphIdx, 1))

                savepos = self.fh.tell()
                self.getGlyphs(glyphIdx, nonlocals)
                self.seek(savepos)
                if flags & GF_WORDS:
                    self.skip(4)
                else:
                    self.skip(2)
                if flags & GF_SCALE:
                    self.skip(2)
                elif flags & GF_XYSCALE:
                    self.skip(4)
                elif flags & GF_TWOBYTWO:
                    self.skip(8)

    def getHMTX(self, numberOfHMetrics, numGlyphs, glyphToChar, scale):
        start = self.seek_table("hmtx")
        aw = 0
        self.charWidths = []

        def resize_cw(size, default):
            size = (((size + 1) // 1024) + 1) * 1024
            delta = size - len(self.charWidths)
            if delta > 0:
                self.charWidths += [default] * delta

        nCharWidths = 0
        if (numberOfHMetrics * 4) < self.maxStrLenRead:
            data = self.get_chunk(start, (numberOfHMetrics * 4))
            arr = unpack(f">{len(data) // 2}H", data)
        else:
            self.seek(start)
        for glyph in range(numberOfHMetrics):
            if (numberOfHMetrics * 4) < self.maxStrLenRead:
                aw = arr[(glyph * 2)]  # PHP starts arrays from index 0!? +1
            else:
                aw = self.read_ushort()
                # pylint: disable=unused-variable
                lsb = self.read_ushort()

            if glyph in glyphToChar or glyph == 0:
                if aw >= (1 << 15):
                    aw = 0  # 1.03 Some (arabic) fonts have -ve values for width
                    # although should be unsigned value
                    # - comes out as e.g. 65108 (intended -50)
                if glyph == 0:
                    self.defaultWidth = scale * aw
                    continue

                for char in glyphToChar[glyph]:
                    if char not in (0, 65535):
                        w = round(scale * aw + 0.001)  # ROUND_HALF_UP
                        if w == 0:
                            w = 65535
                        if char < 196608:
                            if char >= len(self.charWidths):
                                resize_cw(char, self.defaultWidth)
                            self.charWidths[char] = w
                            nCharWidths += 1

        data = self.get_chunk((start + numberOfHMetrics * 4), (numGlyphs * 2))
        arr = unpack(f">{len(data) // 2}H", data)
        diff = numGlyphs - numberOfHMetrics
        for pos in range(diff):
            glyph = pos + numberOfHMetrics
            if glyph in glyphToChar:
                for char in glyphToChar[glyph]:
                    if char not in (0, 65535):
                        w = round(scale * aw + 0.001)  # ROUND_HALF_UP
                        if w == 0:
                            w = 65535
                        if char < 196608:
                            if char >= len(self.charWidths):
                                resize_cw(char, self.defaultWidth)
                            self.charWidths[char] = w
                            nCharWidths += 1

        # NB 65535 is a set width of 0
        # First bytes define number of chars in font
        self.charWidths[0] = nCharWidths

    def getHMetric(self, numberOfHMetrics, gid):
        start = self.seek_table("hmtx")
        if gid < numberOfHMetrics:
            self.seek(start + (gid * 4))
            hm = self.fh.read(4)
        else:
            self.seek(start + ((numberOfHMetrics - 1) * 4))
            hm = self.fh.read(2)
            self.seek(start + (numberOfHMetrics * 2) + (gid * 2))
            hm += self.fh.read(2)
        return hm

    def getLOCA(self, indexToLocFormat, numGlyphs):
        try:
            start = self.seek_table("loca")
        except KeyError:
            # pylint: disable=raise-missing-from
            raise RuntimeError(
                f"Unknown location table format, index={indexToLocFormat}"
            )
        self.glyphPos = []
        if indexToLocFormat == 0:
            data = self.get_chunk(start, (numGlyphs * 2) + 2)
            arr = unpack(f">{len(data) // 2}H", data)
            for n in range(numGlyphs):
                self.glyphPos.append(arr[n] * 2)  # n+1 !?
        elif indexToLocFormat == 1:
            data = self.get_chunk(start, (numGlyphs * 4) + 4)
            arr = unpack(f">{len(data) // 4}L", data)
            for n in range(numGlyphs):
                self.glyphPos.append(arr[n])  # n+1 !?
        else:
            raise RuntimeError(
                f"Unknown location table format, index={indexToLocFormat}"
            )

    # CMAP Format 4
    def getCMAP4(self, unicode_cmap_offset, glyphToChar, charToGlyph):
        self.maxUniChar = 0
        self.seek(unicode_cmap_offset + 2)
        length = self.read_ushort()
        limit = unicode_cmap_offset + length
        self.skip(2)

        segCount = self.read_ushort() // 2
        self.skip(6)
        endCount = []
        for _ in range(segCount):
            endCount.append(self.read_ushort())
        self.skip(2)
        startCount = []
        for _ in range(segCount):
            startCount.append(self.read_ushort())
        idDelta = []
        for _ in range(segCount):
            idDelta.append(self.read_short())  # ???? was unsigned short
        idRangeOffset_start = self._pos
        idRangeOffset = []
        for _ in range(segCount):
            idRangeOffset.append(self.read_ushort())

        for n in range(segCount):
            endpoint = endCount[n] + 1
            for unichar in range(startCount[n], endpoint, 1):
                if idRangeOffset[n] == 0:
                    glyph = (unichar + idDelta[n]) & 0xFFFF
                else:
                    offset = (unichar - startCount[n]) * 2 + idRangeOffset[n]
                    offset = idRangeOffset_start + 2 * n + offset
                    if offset >= limit:
                        glyph = 0
                    else:
                        glyph = self.get_ushort(offset)
                        if glyph != 0:
                            glyph = (glyph + idDelta[n]) & 0xFFFF

                charToGlyph[unichar] = glyph
                if unichar < 196608:
                    self.maxUniChar = max(unichar, self.maxUniChar)
                glyphToChar.setdefault(glyph, []).append(unichar)

    # CMAP Format 12
    def getCMAP12(self, unicode_cmap_offset, glyphToChar, charToGlyph):
        self.maxUniChar = 0
        # table (skip format version, should be 12)
        self.seek(unicode_cmap_offset + 2)
        # reserved
        self.skip(2)
        # table length
        length = self.read_ulong()
        # language (should be 0)
        self.skip(4)
        # groups count
        grpCount = self.read_ulong()

        if 2 + 2 + 4 + 4 + 4 + grpCount * 3 * 4 > length:
            raise RuntimeError("TTF format 12 cmap table too small")
        for _ in range(grpCount):
            startCharCode = self.read_ulong()
            endCharCode = self.read_ulong()
            glyph = self.read_ulong()
            for unichar in range(startCharCode, endCharCode + 1):
                charToGlyph[unichar] = glyph
                if unichar < 196608:
                    self.maxUniChar = max(unichar, self.maxUniChar)
                glyphToChar.setdefault(glyph, []).append(unichar)
                glyph += 1

    # Put the TTF file together
    def endTTFile(self, stm):
        stm = b("")
        numTables = len(self.otables)
        searchRange = 1
        entrySelector = 0
        while searchRange * 2 <= numTables:
            searchRange *= 2
            entrySelector += 1

        searchRange *= 16
        rangeShift = numTables * 16 - searchRange

        # Header
        if _TTF_MAC_HEADER:
            stm += pack(
                ">LHHHH", 0x74727565, numTables, searchRange, entrySelector, rangeShift
            )  # Mac
        else:
            stm += pack(
                ">LHHHH", 0x00010000, numTables, searchRange, entrySelector, rangeShift
            )  # Windows

        # Table directory
        tables = self.otables

        offset = 12 + numTables * 16
        sorted_tables = sorted(tables.items())
        for tag, data in sorted_tables:
            if tag == "head":
                head_start = offset
            stm += tag.encode("latin1")
            checksum = calcChecksum(data)
            stm += pack(">HH", checksum[0], checksum[1])
            stm += pack(">LL", offset, len(data))
            paddedLength = (len(data) + 3) & ~3
            offset = offset + paddedLength

        # Table data
        for tag, data in sorted_tables:
            data += b("\0\0\0")
            stm += substr(data, 0, (len(data) & ~3))

        checksum = calcChecksum(stm)
        checksum = sub32((0xB1B0, 0xAFBA), checksum)
        chk = pack(">HH", checksum[0], checksum[1])
        stm = self.splice(stm, (head_start + 8), chk)
        return stm
