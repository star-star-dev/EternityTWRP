#!/usr/bin/env python3
"""Recompress the recovery ramdisk as LZMA.

The recovery kernel used for d2xks brings up an LZMA ramdisk but stops at the
first screen when the ramdisk is gzip, and the build system keeps producing a
gzip ramdisk even with BOARD_RAMDISK_USE_LZMA set. This rewrites the boot image
the build produced, swapping only the ramdisk and the fields that depend on its
size.
"""
import gzip
import hashlib
import lzma
import struct
import sys


def decompress(data):
    if data[:2] == b"\x1f\x8b":
        return gzip.decompress(data)
    if data[:4] == b"\x5d\x00\x00\x80":
        return lzma.decompress(data, format=lzma.FORMAT_ALONE)
    if data[:6] == b"\xfd7zXZ\x00":
        return lzma.decompress(data)
    return data


def main(src, dst):
    d = open(src, "rb").read()
    ks, _, rs, _, _, _, _, ps, hv, osv = struct.unpack("<10I", d[8:48])
    dtbo_size, dtbo_off = struct.unpack("<IQ", d[0x660:0x66C])
    hdr_size = struct.unpack("<I", d[0x66C:0x670])[0]
    page = lambda n: (n + ps - 1) // ps

    ko = page(1) * ps
    ro = ko + page(ks) * ps
    kernel = d[ko:ko + ks]
    ramdisk = d[ro:ro + rs]
    dtbo = d[dtbo_off:dtbo_off + dtbo_size]

    cpio = decompress(ramdisk)
    newram = lzma.compress(cpio, format=lzma.FORMAT_ALONE, preset=6)

    def hash_part(sha, blob):
        sha.update(blob)
        sha.update(struct.pack("<I", len(blob)))

    sha = hashlib.sha1()
    hash_part(sha, kernel)
    hash_part(sha, newram)
    sha.update(struct.pack("<I", 0))
    hash_part(sha, dtbo)
    image_id = sha.digest()

    hdr = bytearray(2048)
    hdr[:] = d[:2048]
    for off, val in ((8, ks), (16, len(newram)), (24, 0), (36, ps), (40, hv), (44, osv)):
        struct.pack_into("<I", hdr, off, val)
    hdr[576:608] = image_id + bytes(12)

    ro = ko + page(ks) * ps
    rdo = ro + page(len(newram)) * ps
    total = page(rdo + page(dtbo_size) * ps) * ps
    struct.pack_into("<I", hdr, 0x660, dtbo_size)
    struct.pack_into("<Q", hdr, 0x664, rdo)
    struct.pack_into("<I", hdr, 0x66C, hdr_size)

    out = bytearray(total)
    out[:2048] = hdr
    out[ko:ko + ks] = kernel
    out[ro:ro + len(newram)] = newram
    out[rdo:rdo + dtbo_size] = dtbo
    open(dst, "wb").write(out)
    print(f"ramdisk {rs} -> {len(newram)} bytes (LZMA), image {total} bytes")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
