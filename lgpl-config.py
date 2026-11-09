#!/usr/bin/env python3
"""Turn shinchiro/mpv-winbuild-cmake recipes into an LGPL-only libmpv build.

Every edit is an exact text match: if upstream changes a recipe, the script
fails instead of silently producing a different build. Run from the root of
the mpv-winbuild-cmake checkout.

What changes:
- FFmpeg: no --enable-gpl, GPL-only libraries removed (x264, x265, davs2,
  rubberband, libzvbi, avisynth, dvdnav/dvdread), plus features FilePeak does
  not need (VapourSynth, libbluray, libssh, libsrt).
- mpv: -Dgpl=false, libmpv only (no mpv.exe), and Lua, JavaScript, libcurl,
  libbluray, VapourSynth, dvdnav, rubberband, OpenAL, subrandr, libarchive, SDL2 gamepad, sixel disabled.
- mpv and libplacebo without Vulkan: no vulkan-1.dll import, rendering through Direct3D 11.
- FFmpeg, player only: no external encoders (lame, libvpx, libwebp, aom, SVT-AV1, AMF, NVENC), no network
  (OpenSSL), no QSV (libvpl), no rare formats or filters (modplug, openmpt, JPEG XL, ARIB captions, AVS3,
  bs2b, mysofa, OpenAL). FFmpeg's own decoders cover VP8/VP9, WebP, MP3, AV1 (dav1d).
- libarchive: without LZO (GPL), in case it comes back in the graph.
collect-sources.sh then refuses any known GPL package left in the mpv graph.
"""
import sys
from pathlib import Path


def edit(path, removals=(), replacements=()):
    file = Path(path)
    text = file.read_text()
    for line in removals:
        needle = line + "\n"
        if text.count(needle) != 1:
            sys.exit(f"{path}: expected exactly one line '{line.strip()}'")
        text = text.replace(needle, "")
    for old, new in replacements:
        if text.count(old) != 1:
            sys.exit(f"{path}: expected exactly one occurrence of:\n{old}")
        text = text.replace(old, new)
    file.write_text(text)
    print(f"patched {path}")


def dep(name):
    return f"        {name}"


edit(
    "packages/ffmpeg.cmake",
    removals=[
        dep("avisynth-headers"),
        dep("libssh"),
        dep("libsrt"),
        dep("libbluray"),
        dep("libdvdnav"),
        dep("libdvdread"),
        dep("x264"),
        dep("${ffmpeg_x265}"),
        dep("libzvbi"),
        dep("vapoursynth"),
        dep("${ffmpeg_davs2}"),
        dep("rubberband"),
        # Not needed to play local files: encoders, network, filters and rare formats. Fewer packages, faster
        # build, smaller DLL, and no upstream patch that breaks when the library changes (libvpl, openssl, libbs2b).
        dep("amf-headers"),
        dep("lame"),
        dep("openssl"),
        dep("libmodplug"),
        dep("libbs2b"),
        dep("libvpx"),
        dep("libwebp"),
        dep("libmysofa"),
        dep("libvpl"),
        dep("libopenmpt"),
        dep("libjxl"),
        dep("libaribcaption"),
        dep("aom"),
        dep("svtav1"),
        dep("${ffmpeg_uavs3d}"),
        dep("openal-soft"),
        dep("--enable-libmodplug"),
        dep("--enable-libopenmpt"),
        dep("--enable-libmp3lame"),
        dep("--enable-libbs2b"),
        dep("--enable-libvpx"),
        dep("--enable-libwebp"),
        dep("--enable-libaom"),
        dep("--enable-libsvtav1"),
        dep("${ffmpeg_uavs3d_cmd}"),
        dep("--enable-openssl"),
        dep("--enable-libmysofa"),
        dep("--enable-libvpl"),
        dep("--enable-libjxl"),
        dep("--enable-libaribcaption"),
        dep("--enable-nvenc"),
        dep("--enable-amf"),
        dep("--enable-openal"),
        dep("--disable-decoder=libaom_av1"),
        dep("--enable-gpl"),
        dep("--enable-avisynth"),
        dep("--enable-vapoursynth"),
        dep("--enable-libbluray"),
        dep("--enable-libdvdnav"),
        dep("--enable-libdvdread"),
        dep("--enable-librubberband"),
        dep("--enable-libx264"),
        dep("--enable-libx265"),
        dep("${ffmpeg_davs2_cmd}"),
        dep("--enable-libssh"),
        dep("--enable-libsrt"),
        dep("--enable-libzvbi"),
    ],
)

edit(
    "packages/mpv.cmake",
    removals=[
        dep("libdvdnav"),
        dep("libdvdread"),
        dep("luajit"),
        dep("rubberband"),
        dep("openal-soft"),
        dep("mujs"),
        dep("vapoursynth"),
        dep("subrandr"),
        dep("curl"),
        dep("libarchive"),
        dep("libsdl2"),
        dep("libsixel"),
        # No Vulkan: the DLL would import vulkan-1.dll and fail to load where it is missing. Windows renders with
        # Direct3D 11 (shaderc and spirv-cross stay, d3d11 needs them).
        dep("vulkan"),
        # libmpv only: no mpv.exe package, no debug package.
        "    COMMAND ${CMAKE_COMMAND} -E copy <BINARY_DIR>/mpv.exe                           ${CMAKE_CURRENT_BINARY_DIR}/mpv-package/mpv.exe",
        "    COMMAND ${CMAKE_COMMAND} -E copy <BINARY_DIR>/mpv.com                           ${CMAKE_CURRENT_BINARY_DIR}/mpv-package/mpv.com",
        "    COMMAND ${CMAKE_COMMAND} -E copy <SOURCE_DIR>/etc/mpv-register.bat              ${CMAKE_CURRENT_BINARY_DIR}/mpv-package/mpv-register.bat",
        "    COMMAND ${CMAKE_COMMAND} -E copy <SOURCE_DIR>/etc/mpv-unregister.bat            ${CMAKE_CURRENT_BINARY_DIR}/mpv-package/mpv-unregister.bat",
        "    COMMAND ${CMAKE_COMMAND} -E copy <BINARY_DIR>/mpv.pdf                           ${CMAKE_CURRENT_BINARY_DIR}/mpv-package/doc/manual.pdf",
        "    COMMAND ${CMAKE_COMMAND} -E copy ${MINGW_INSTALL_PREFIX}/etc/fonts/fonts.conf   ${CMAKE_CURRENT_BINARY_DIR}/mpv-package/mpv/fonts.conf",
        "    ${mpv_copy_debug}",
        "    COMMAND mv ${CMAKE_CURRENT_BINARY_DIR}/mpv-package ${CMAKE_BINARY_DIR}/mpv-${TARGET_CPU}${x86_64_LEVEL}-${BUILDDATE}",
        "    COMMAND ${RENAME} <SOURCE_DIR> ${CMAKE_BINARY_DIR}/mpv-${TARGET_CPU}${x86_64_LEVEL}-${BUILDDATE}",
        "    COMMAND mv ${CMAKE_CURRENT_BINARY_DIR}/mpv-debug ${CMAKE_BINARY_DIR}/mpv-debug-${TARGET_CPU}${x86_64_LEVEL}-${BUILDDATE}",
        "    COMMAND ${RENAME} <SOURCE_DIR> ${CMAKE_BINARY_DIR}/mpv-debug-${TARGET_CPU}${x86_64_LEVEL}-${BUILDDATE}",
    ],
    replacements=[
        ("        --prefer-static\n", "        --prefer-static\n        -Dgpl=false\n        -Dcplayer=false\n"),
        ("-Dpdf-build=enabled", "-Dpdf-build=disabled"),
        ("-Dlua=enabled", "-Dlua=disabled"),
        ("-Djavascript=enabled", "-Djavascript=disabled"),
        ("-Dlibbluray=enabled", "-Dlibbluray=disabled"),
        ("-Ddvdnav=enabled", "-Ddvdnav=disabled"),
        ("-Drubberband=enabled", "-Drubberband=disabled"),
        ("-Dopenal=enabled", "-Dopenal=disabled"),
        ("-Dvapoursynth=enabled", "-Dvapoursynth=disabled"),
        ("-Dsubrandr=enabled", "-Dsubrandr=disabled"),
        ("-Dlibcurl=enabled", "-Dlibcurl=disabled"),
        ("-Dsdl2-gamepad=enabled", "-Dsdl2-gamepad=disabled"),
        ("-Dlibarchive=enabled", "-Dlibarchive=disabled"),
        ("-Dsixel=enabled", "-Dsixel=disabled"),
        ("-Dvulkan=enabled", "-Dvulkan=disabled"),
        (
            "${CMAKE_BINARY_DIR}/mpv-dev-${TARGET_CPU}${x86_64_LEVEL}-${BUILDDATE}\n    COMMAND ${RENAME} <SOURCE_DIR> ${CMAKE_BINARY_DIR}/mpv-dev-${TARGET_CPU}${x86_64_LEVEL}-${BUILDDATE}",
            "${CMAKE_BINARY_DIR}/mpv-dev-lgpl-${TARGET_CPU}${x86_64_LEVEL}-${BUILDDATE}\n    COMMAND ${RENAME} <SOURCE_DIR> ${CMAKE_BINARY_DIR}/mpv-dev-lgpl-${TARGET_CPU}${x86_64_LEVEL}-${BUILDDATE}",
        ),
    ],
)

# libplacebo: Direct3D 11 only, no Vulkan (see mpv above).
edit(
    "packages/libplacebo.cmake",
    removals=[dep("vulkan")],
    replacements=[
        ("        -Dd3d11=enabled\n", "        -Dd3d11=enabled\n        -Dvulkan=disabled\n"),
        # The registry comes from the Vulkan headers, no longer installed.
        ("        -Dvulkan-registry='${MINGW_INSTALL_PREFIX}/share/vulkan/registry/vk.xml'\n", ""),
    ],
)

# libarchive (used by mpv): LZO is GPL.
edit(
    "packages/libarchive.cmake",
    removals=[dep("lzo")],
    replacements=[("-DENABLE_LZO=ON", "-DENABLE_LZO=OFF")],
)

# GCC toolchain: mpv.exe is not built any more, only strip the DLL.
edit(
    "cmake/packages_check.cmake",
    replacements=[
        (
            "    set(mpv_add_debuglink COMMAND ${EXEC} ${TARGET_ARCH}-objcopy --only-keep-debug <BINARY_DIR>/mpv.exe <BINARY_DIR>/mpv.debug\n"
            "                          COMMAND ${EXEC} ${TARGET_ARCH}-strip -s <BINARY_DIR>/mpv.exe\n"
            "                          COMMAND ${EXEC} ${TARGET_ARCH}-objcopy --add-gnu-debuglink=<BINARY_DIR>/mpv.debug <BINARY_DIR>/mpv.exe\n"
            "                          COMMAND ${EXEC} ${TARGET_ARCH}-strip -s <BINARY_DIR>/mpv.com\n"
            "                          COMMAND ${EXEC} ${TARGET_ARCH}-strip -s <BINARY_DIR>/libmpv-2.dll)\n",
            "    set(mpv_add_debuglink COMMAND ${EXEC} ${TARGET_ARCH}-strip -s <BINARY_DIR>/libmpv-2.dll)\n",
        )
    ],
)
