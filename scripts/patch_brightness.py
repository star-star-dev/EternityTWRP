#!/usr/bin/env python3
"""Keep the backlight out of the blank path.

blanktimer turns the panel off by writing "5" and then "0" to the backlight
node. On this panel a 0 write latches the lowest luminance and the panel never
returns from it, so waking leaves the screen stuck at minimum brightness with a
dead slider. The CRTC blank in the same code is what actually turns the screen
off and is fine, so only the three backlight writes are dropped. The wake-up
restore and the brightness slider keep working.

The writes are removed in the source rather than patched at fixed offsets in
the compiled binary, because any change elsewhere shifts those offsets.

Usage: patch_brightness.py [path to bootable/recovery]
"""
import os
import sys

PATH = os.path.join("gui", "blanktimer.cpp")

# The two "0" sites are identical, so both are replaced; the "5" site is unique.
REPLACEMENTS = [
    (
        "\t\tstate = kOff;\n"
        '\t\tTWFunc::Set_Brightness("0");\n',
        "\t\tstate = kOff;\n"
        "\t\t// Backlight write dropped: a 0 write latches the panel at minimum\n"
        "\t\t// luminance. The CRTC blank below still turns the screen off.\n",
    ),
    (
        "\t\tstate = kDim;\n"
        '\t\tTWFunc::Set_Brightness("5");\n',
        "\t\tstate = kDim;\n"
        "\t\t// Backlight write dropped, see above.\n",
    ),
]


def main(recovery_dir="bootable/recovery"):
    path = os.path.join(recovery_dir, PATH)
    with open(path, "r") as f:
        src = f.read()

    for old, new in REPLACEMENTS:
        if new in src:
            print(f"already patched: {old.strip().splitlines()[-1]}")
            continue
        count = src.count(old)
        if count == 0:
            raise SystemExit(f"{PATH}: pattern not found:\n{old}")
        src = src.replace(old, new)
        print(f"patched {count} site(s): {old.strip().splitlines()[-1]}")

    with open(path, "w") as f:
        f.write(src)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bootable/recovery")
