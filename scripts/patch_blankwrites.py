#!/usr/bin/env python3
"""Skip blanktimer's backlight writes but keep the CRTC blank.

blanktimer dims the panel by writing "5" and then "0" to the backlight node.
On this panel a 0 write latches the lowest luminance and the panel never
returns from it, so waking leaves the screen stuck at minimum brightness with
a dead slider. The CRTC blank itself is fine and is what actually turns the
screen off, so keep it and only drop the two writes.

The wake-up restore (Set_Brightness(orig_brightness) in
resetTimerAndUnblank) is deliberately left intact, as is the brightness
slider. The three call sites patched here are the only blanktimer writes.

Usage: patch_blankwrites.py <in.img> <out.img>
"""
import gzip
import hashlib
import lzma
import struct
import sys

NOP = bytes.fromhex("d503201f")  # ARM64 nop

PATCHES = {
    "system/bin/recovery": [
        (0x1DC508, bytes.fromhex("f3a9fc97"), "blanktimer::checkForTimeout dim \"5\""),
        (0x1DC558, bytes.fromhex("dfa9fc97"), "blanktimer::checkForTimeout off \"0\""),
        (0x1DC7BC, bytes.fromhex("46a9fc97"), "blanktimer::blank off \"0\""),
    ],
}


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

    cpio = bytearray(decompress(ramdisk))

    off = 0
    done = set()
    while off + 110 <= len(cpio):
        if cpio[off:off + 6] != b"070701":
            break
        h = lambda i: int(cpio[off + 6 + i * 8:off + 6 + i * 8 + 8], 16)
        filesize = h(6)
        namesize = h(11)
        off += 110
        name = cpio[off:off + namesize - 1].decode("utf-8", "replace")
        off += namesize
        off = (off + 3) & ~3
        if name in PATCHES:
            for p_off, expect, label in PATCHES[name]:
                cur = bytes(cpio[off + p_off:off + p_off + 4])
                if cur != expect:
                    raise SystemExit(
                        f"{name} @{p_off:#x} ({label}): got {cur.hex()} want {expect.hex()}")
                cpio[off + p_off:off + p_off + 4] = NOP
                print(f"patched {label} @{p_off:#x}")
            done.add(name)
        off += filesize
        off = (off + 3) & ~3

    missing = set(PATCHES) - done
    if missing:
        raise SystemExit(f"missing members: {missing}")

    newram = lzma.compress(bytes(cpio), format=lzma.FORMAT_ALONE, preset=6)
    if lzma.decompress(newram, format=lzma.FORMAT_ALONE) != bytes(cpio):
        raise SystemExit("ramdisk round-trip mismatch")

    def hash_part(sha, blob):
        sha.update(blob)
        sha.update(struct.pack("<I", len(blob)))

    sha = hashlib.sha1()
    hash_part(sha, kernel)
    hash_part(sha, newram)
    sha.update(struct.pack("<I", 0))
    hash_part(sha, dtbo)
    image_id = sha.digest()

    hdr = bytearray(d[:2048])
    for o, v in ((8, ks), (16, len(newram)), (24, 0), (36, ps), (40, hv), (44, osv)):
        struct.pack_into("<I", hdr, o, v)
    hdr[576:608] = image_id

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
