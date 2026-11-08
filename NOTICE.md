# libmpv-2.dll — third-party notices

`libmpv-2.dll` is a build of **mpv** (https://mpv.io) and **FFmpeg** (https://ffmpeg.org) with their
dependencies, linked statically into a single DLL, built from
https://github.com/devistar/libmpv-build.

- mpv is licensed under the GNU Lesser General Public License, version 2.1 or later (built with `-Dgpl=false`).
- FFmpeg is licensed under the GNU Lesser General Public License, version 3 or later (built without `--enable-gpl` and without `--enable-nonfree`).
- As a whole, `libmpv-2.dll` is therefore distributed under the GNU LGPL, version 3 or later.
- The other components keep their own licenses (BSD, MIT, ISC, zlib, Apache 2.0, LGPL...). Each folder of this archive holds the license files of one component; `MANIFEST.txt` lists every component with the exact source commit.

The complete corresponding source of each release (every component at the exact commit used,
and the build recipes) is published with the release, next to the DLL:
https://github.com/devistar/libmpv-build/releases

You may replace `libmpv-2.dll` with your own build of libmpv (same API, `libmpv-2.dll` file name):
applications using this DLL load it at runtime and do not check its signature or contents.
