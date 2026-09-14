# Desktop Builds & Packaging

## Windows Build
* Built via PyInstaller:
  ```powershell
  python desktop/build_windows.py
  ```
* Output binary: `desktop/dist/HCS-WorldJumper/HCS-WorldJumper.exe`
* Packaged release archive: `installer/HCS-WorldJumper-v1.0.0-windows-x64.zip`
* Runtime Backend: Microsoft Edge Chromium WebView2 engine with full hardware GPU acceleration.

## Linux Build
* Launcher script: `desktop/HCS-WorldJumper-linux.sh`
* Packaged release archive: `installer/HCS-WorldJumper-v1.0.0-linux-x86_64.tar.gz`
* Runtime Backend: WebKitGTK / Qt WebEngine.

## Checksums
Verified in `installer/SHA256SUMS.txt`:
```
d71ca84e5a46860b7564db3552737f03cf74fa5b28afb7505ea3f80ad61afc31  HCS-WorldJumper-v1.0.0-windows-x64.zip
28a2e3aaddbb06caca533a126558678637c9ca1e607c09b42a5d1d9aa8c11327  HCS-WorldJumper-v1.0.0-linux-x86_64.tar.gz
```
