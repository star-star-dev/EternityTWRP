# TWRP Device Tree for Samsung Galaxy Note 10+ 5g (d2xks)
## How to build
This device tree was tested and is fully compatible with [minimal-manifest-twrp](https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp).
1. Set up the build environment following the instructions [here](https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp/blob/twrp-11/README.md#getting-started)
2. In the root folder of the fetched repo, clone the device tree:
```bash
git clone https://github.com/Ocin4ever/EternityTWRP.git -b d2xks device/samsung/d2xks
```
3. Apply the source patches the image depends on. The CI workflow does this
   automatically; run them by hand when building locally:
```bash
python3 device/samsung/d2xks/scripts/patch_language.py bootable/recovery
python3 device/samsung/d2xks/scripts/patch_brightness.py bootable/recovery
```
4. To build:
```bash
. build/envsetup.sh
lunch twrp_d2xks-eng
mka recoveryimage
```
5. Rewrite the ramdisk as LZMA. The build produces a gzip ramdisk even with
   `BOARD_RAMDISK_USE_LZMA`, and the recovery kernel stops at the first screen
   unless the ramdisk is LZMA:
```bash
python3 device/samsung/d2xks/scripts/lzma_ramdisk.py \
    out/target/product/d2xks/recovery.img recovery.img
```

## Flashing

Flash both images from the release. A recovery image whose length is not a
multiple of the 2048-byte page size is rejected by the bootloader, which shows
up as a black screen that never reaches TWRP. The bundled `vbmeta.img` disables
verification, so the recovery image does not need a signature that matches the
device key.

```bash
# Odin: Star7TWRP-d2xks.img -> AP, vbmeta.img -> AP (or CP for the stock layout)
# fastboot:
fastboot flash recovery Star7TWRP-d2xks.img
fastboot flash vbmeta vbmeta.img
```

After this pair has been flashed once, later recovery images can be flashed on
their own.

## Language

The UI defaults to Chinese (`TW_DEFAULT_LANGUAGE := zh_CN` in `BoardConfig.mk`).
A fresh install and a settings file left behind by an older build both come up
in Chinese, because TWRP only keeps the compiled default once a language has
been chosen on purpose.

Selecting another language, for example English, persists: the choice is saved
immediately and wins over the default from then on. `scripts/patch_language.py`
adds both behaviours to the TWRP source before the build.

## Copyright

```
#
# Copyright (C) 2024 The TWRP Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
```
