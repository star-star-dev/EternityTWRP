#!/usr/bin/env python3
"""Pad a boot image to the 2048-byte boundary the bootloader expects.

The original recovery image ends on a 2048-byte boundary with a short run of
zero padding after the recovery_dtbo. The repacked image is not aligned, so
extend it with zeros to match.

Usage: pad_image.py <in.img> <out.img>
"""
import sys

ALIGN = 2048


def main(src, dst):
    d = open(src, "rb").read()
    rem = len(d) % ALIGN
    if rem:
        d += bytes(ALIGN - rem)
    open(dst, "wb").write(d)
    print(f"padded to {len(d)} bytes")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
