#!/usr/bin/env python3
"""Default the UI to Chinese without stopping the user from choosing another
language.

Two independent behaviours need fixing in TWRP 12.1:

1. The compiled default (TW_DEFAULT_LANGUAGE) is only written to the in-memory
   settings. When a settings file already exists, LoadValues() replaces it with
   whatever is on disk, so a device that ever ran a build defaulting to English
   keeps coming up in English no matter what this build was compiled with.

2. Picking a language runs GUIAction::setlanguage, which loads the language and
   requests a theme reload but never writes the choice to disk. The reload then
   calls PageManager::RunReload(), which ends in DataManager::ReadSettingsFile()
   and re-reads the settings file, discarding the choice before it is saved. The
   next boot therefore shows the previous language again.

The fix records whether a language was ever chosen on purpose
(tw_language_set). Until it is set, the compiled default is re-applied after
the settings file is read, so a fresh device and a stale settings file both boot
in the default language. Choosing a language sets the flag and saves the
settings immediately, so from then on the saved choice wins.

Usage: patch_language.py [path to bootable/recovery]
"""
import os
import sys

PATCHES = [
    (
        "data.cpp",
        '\tLOGINFO("Attempt to load settings from settings file...\\n");\n'
        "\tLoadValues(settings_file);\n",
        '\tLOGINFO("Attempt to load settings from settings file...\\n");\n'
        "\tLoadValues(settings_file);\n"
        "\t// A fresh device and a settings file written by an older build both\n"
        "\t// leave tw_language_set empty. Keep the compiled default until a\n"
        "\t// language is chosen on purpose.\n"
        '\tif (GetStrValue("tw_language_set").empty())\n'
        '\t\tmPersist.SetValue("tw_language", EXPAND(TW_DEFAULT_LANGUAGE));\n',
    ),
    (
        os.path.join("gui", "action.cpp"),
        '\tPageManager::LoadLanguage(DataManager::GetStrValue("tw_language"));\n'
        "\tPageManager::RequestReload();\n",
        '\tPageManager::LoadLanguage(DataManager::GetStrValue("tw_language"));\n'
        '\tDataManager::SetValue("tw_language_set", "1", 1);\n'
        "\tDataManager::Flush();\n"
        "\tPageManager::RequestReload();\n",
    ),
]


def patch(recovery_dir, rel, old, new):
    path = os.path.join(recovery_dir, rel)
    with open(path, "r") as f:
        src = f.read()

    if new in src:
        print(f"already patched: {rel}")
        return

    if src.count(old) != 1:
        raise SystemExit(f"{rel}: expected exactly one match, found {src.count(old)}")

    with open(path, "w") as f:
        f.write(src.replace(old, new))
    print(f"patched: {rel}")


def main(recovery_dir="bootable/recovery"):
    for rel, old, new in PATCHES:
        patch(recovery_dir, rel, old, new)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bootable/recovery")
