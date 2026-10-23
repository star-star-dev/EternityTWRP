#!/usr/bin/env python3
"""Make the language selection persist across reboots.

Picking a language runs GUIAction::setlanguage, which only loads the new
language and requests a theme reload. It never writes the choice to the
settings file, so the selection lives in memory only.

The reload then calls PageManager::RunReload(), which ends with
DataManager::ReadSettingsFile(). That re-reads .twrps and overwrites the
in-memory tw_language with the value already on disk. By the time the user
reboots, the freshly chosen language has been replaced by the old one, so the
next boot comes up in the previous language.

Saving the settings right after the language is loaded writes the new value to
.twrps before the reload re-reads it, so the reload no longer undoes the
selection and the next boot keeps it.

Usage: patch_language_persist.py [path to bootable/recovery]
"""
import os
import re
import sys

OLD = (
    '\tPageManager::LoadLanguage(DataManager::GetStrValue("tw_language"));\n'
    '\tPageManager::RequestReload();\n'
)
NEW = (
    '\tPageManager::LoadLanguage(DataManager::GetStrValue("tw_language"));\n'
    '\tDataManager::Flush();\n'
    '\tPageManager::RequestReload();\n'
)


def main(recovery_dir="bootable/recovery"):
    path = os.path.join(recovery_dir, "gui", "action.cpp")
    with open(path, "r") as f:
        src = f.read()

    func = re.search(r"int GUIAction::setlanguage\(.*?\n\}\n", src, re.S)
    if not func:
        raise SystemExit(f"setlanguage() not found in {path}")

    if "DataManager::Flush();" in func.group(0):
        print("already patched, nothing to do")
        return

    body = func.group(0)
    if OLD not in body:
        raise SystemExit(f"unexpected setlanguage() body in {path}")

    src = src[: func.start()] + body.replace(OLD, NEW) + src[func.end():]
    with open(path, "w") as f:
        f.write(src)
    print(f"patched {path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "bootable/recovery")
