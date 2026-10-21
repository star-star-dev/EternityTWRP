#!/usr/bin/env python3
"""Re-sign the finished recovery image with an AVB hash footer.

lzma_ramdisk.py rebuilds the boot image from scratch, which drops the AVB
footer the build had added and leaves the image shorter than the recovery
partition. The bootloader reads that footer from the end of the partition,
so a recovery image without it does not come up and the screen stays black.
Re-signing with the same key and partition size the build used restores it.
"""
import os
import subprocess
import sys

PARTITION_SIZE = 67633152
ALGORITHM = "SHA256_RSA4096"
ROLLBACK_INDEX = "1"
PROPS = (
    "com.android.build.boot.os_version:99.87.36",
    "com.android.build.boot.security_patch:2099-12-31",
)


def find_avbtool(root):
    for rel in ("external/avb/avbtool.py", "external/avb/avbtool"):
        path = os.path.join(root, rel)
        if os.path.exists(path):
            return path
    return None


def main(image, root, key):
    avbtool = find_avbtool(root)
    if avbtool is None:
        sys.exit("avbtool not found under " + root)
    size = os.path.getsize(image)
    if size > PARTITION_SIZE:
        sys.exit(f"{image} is {size} bytes, larger than the partition")

    cmd = [sys.executable, avbtool, "add_hash_footer",
           "--image", image,
           "--partition_name", "recovery",
           "--partition_size", str(PARTITION_SIZE),
           "--algorithm", ALGORITHM,
           "--key", key,
           "--rollback_index", ROLLBACK_INDEX]
    for prop in PROPS:
        cmd += ["--prop", prop]
    subprocess.run(cmd, check=True)
    print(f"{image}: {size} -> {os.path.getsize(image)} bytes (AVB signed)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
