# Release notes

## Source selection

`UpdateSlicePlane/UpdateSlicePlane/UpdateSlicePlane` and `VXMController/VXMController/VXMController` contain the packaged modules and their resources. Their main Python files are identical to the corresponding top-level files. The GUI uses the `VelmexController` class embedded in `VXMController.py`; the separate backup controller is therefore not included.

`docs/source-manifest.json` records original paths relative to the supplied KIST folder and SHA-256 hashes. Files were prepared in a separate release directory; original materials were not modified.

## Publication edits

- Removed hardcoded Anaconda `site-packages` paths.
- Read the serial port from `VXM_SERIAL_PORT`, preserving the original COM4 default.
- Replaced the instrument-specific VISA identifier with required `VXM_VISA_RESOURCE`.
- Redirected scan saves to Slicer's temporary directory.
- Replaced placeholder module help link and repaired contributor text punctuation.
- Kept template acknowledgements and included the upstream Slicer license.

Movement commands, scan loops, transform math and waveform interpretation are preserved. These limited changes are not a hardware-control redesign.

## Known limitations

- `Oscilloscope.getData` requests ASCII transfer but parses 5,000 signed binary bytes after a fixed five-byte prefix. The correct transfer mode/header handling must be checked against the actual oscilloscope. Acquisition was not tested here.
- The original serial/open failures may call `exit()`; startup is not resilient to disconnected instruments.
- The stage timing function returns -1 above 30 mm, although the UI allows larger step entries. Use only apparatus-validated movement ranges; no claim is made that every UI value is supported.
- Position bookkeeping and device limits are not a replacement for mechanical calibration or interlocks.
- GUI updates use the original Slicer APIs. There is no claim of compatibility with all newer Slicer versions.
- Repeated scan saves overwrite a temporary NumPy output file.

## Figure provenance

All figures are extracted without image modification from `알키미스트 0225.pptx`: interface (slide 26), fiducial controls (slide 30), acquired waveform (slide 34). The historical screenshot contains no patient image. Slide 27 supplies the reported scan-duration comparison. The full internal presentation and participant/medical-image figures are not redistributed.
