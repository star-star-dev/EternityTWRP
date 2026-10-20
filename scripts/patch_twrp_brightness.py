#!/usr/bin/env python3
"""Fix the truncated backlight value written by fbdev_blank().

With TW_NO_SCREEN_BLANK the framebuffer is not powered down; blanking is done
by writing the backlight node instead. That code formats the value into a
4-byte buffer with "%03d" and always writes 3 bytes, so any value above 999
(e.g. TW_MAX_BRIGHTNESS/2 = 12750) is truncated and the panel comes back very
dark. Reformat into a large enough buffer and write the whole value.
"""
import re
import sys

PATH = "minuitwrp/graphics_fbdev.cpp"

OLD = '''    int fd;
    char brightness[4];
    snprintf(brightness, 4, "%03d", TW_MAX_BRIGHTNESS/2);'''

NEW = '''    int fd;
    char brightness[16];
    snprintf(brightness, sizeof(brightness), "%d", TW_MAX_BRIGHTNESS/2);'''

OLD_WRITE = 'write(fd, blank ? "000" : brightness, 3);'
NEW_WRITE = 'write(fd, blank ? "0" : brightness, blank ? 1 : strlen(brightness));'


def main(tree):
    path = f"{tree}/{PATH}"
    text = open(path).read()
    if OLD_WRITE not in text:
        print("already patched or unexpected source; nothing to do")
        return
    text = text.replace(OLD, NEW).replace(OLD_WRITE, NEW_WRITE)
    open(path, "w").write(text)
    print(f"patched {path}")


if __name__ == "__main__":
    main(sys.argv[1])
