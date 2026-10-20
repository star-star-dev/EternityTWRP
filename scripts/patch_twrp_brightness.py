#!/usr/bin/env python3
"""Fix the truncated backlight value written by fbdev_blank().

With TW_NO_SCREEN_BLANK the framebuffer is not powered down; blanking is done
by writing the backlight node instead. That code formats the value into a
4-byte buffer with "%03d" and always writes 3 bytes, so any value above 999
(e.g. TW_MAX_BRIGHTNESS/2 = 12750) is truncated and the panel comes back very
dark. Reformat into a large enough buffer and write the whole value.
"""
import os
import sys

CANDIDATES = (
    "minuitwrp/graphics_fbdev.cpp",
    "minui/graphics_fbdev.cpp",
)

OLD = '''    int fd;
    char brightness[4];
    snprintf(brightness, 4, "%03d", TW_MAX_BRIGHTNESS/2);'''

NEW = '''    int fd;
    char brightness[16];
    snprintf(brightness, sizeof(brightness), "%d", TW_MAX_BRIGHTNESS/2);'''

OLD_WRITE = 'write(fd, blank ? "000" : brightness, 3);'
NEW_WRITE = 'write(fd, blank ? "0" : brightness, blank ? 1 : strlen(brightness));'


def find_sources(tree):
    for rel in CANDIDATES:
        path = os.path.join(tree, rel)
        if os.path.exists(path):
            return [path]
    found = []
    skip = {".git", ".repo", "out", "prebuilts", "external"}
    for root, dirs, files in os.walk(tree):
        dirs[:] = [d for d in dirs if d not in skip]
        if "graphics_fbdev.cpp" in files:
            found.append(os.path.join(root, "graphics_fbdev.cpp"))
    return found


def main(tree):
    paths = find_sources(tree)
    if not paths:
        raise SystemExit("graphics_fbdev.cpp not found")
    patched = 0
    for path in paths:
        text = open(path).read()
        if OLD_WRITE not in text:
            print(f"{os.path.relpath(path, tree)}: pattern not present")
            continue
        text = text.replace(OLD, NEW).replace(OLD_WRITE, NEW_WRITE)
        open(path, "w").write(text)
        print(f"patched {os.path.relpath(path, tree)}")
        patched += 1
    if patched == 0:
        raise SystemExit("no graphics_fbdev.cpp matched the expected code")


if __name__ == "__main__":
    main(sys.argv[1])
