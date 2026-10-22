# Lenovo Y50-70 — macOS Tahoe EFI

**Experimental. Display acceleration is not working in this setup.** These files
are shared as-is, not as a promise that every Y50 configuration will boot.
Keep a working USB bootloader and a private backup before making changes.

## Downloads

- **[EFI.zip](EFI.zip)** — current internal EFI snapshot, October 22, 2026.
  SMBIOS model: `MacBookPro14,3`.
- **[EFI-pre-patch.zip](EFI-pre-patch.zip)** — the repository's previous EFI,
  renamed and privacy-sanitized. Its original settings and `MacBookPro11,5`
  model are retained, except for removal of machine-specific identifiers.

Both archives have **blank serial, MLB, UUID and ROM fields**. Do not boot these
templates or sign into Apple services before generating your own identity.
Old configs, inactive backup bundles and machine-specific Bluetooth controller
data are excluded from the current distribution. No boot logs or firmware
reports are included. Other boot settings are retained from the snapshot.

## Generate your own SMBIOS automatically

1. Download one archive and extract it. You should have an `EFI` folder with
   `BOOT` and `OC` inside.
2. Download [`generate-smbios.py`](generate-smbios.py) into the same parent folder.
3. Install Python 3 if needed, then run:

   ```sh
   python3 generate-smbios.py --efi EFI --output EFI-personalized
   ```

   On Windows use `py -3` instead of `python3`.

The tool automatically downloads **official Acidanthera macserial from OpenCore
1.0.8**, checks the pinned archive SHA-256 before running it, and generates a
serial/MLB pair for the template's model, a random UUID, and a random locally
administered ROM. Internet access is required for the download. Alternatively,
pass `--macserial /path/to/macserial` to use an official compatible local binary.
The bundled upstream binaries may require an x86-compatible system or translation.

The source template is never changed. Your private boot files are written to
`EFI-personalized` (rename this directory to `EFI` when copying it to your EFI
partition). Never put the personalized copy on GitHub. Keep the same generated
identity for future updates; do not generate a new one at every boot.

Random generation makes collisions unlikely, **not impossible**, and does not
register a legitimate Apple device. Check the serial with Apple's coverage
service; if it belongs to a real device, discard the private output and generate
another. Validate the resulting config with the matching OpenCore `ocvalidate`
before use. Apple services are not guaranteed to work.

## Installation precautions

Test on a USB first. Copy the generated folder as `EFI` at the root of the EFI
partition, not as `EFI/EFI`. Review ACPI, kexts, graphics, Wi-Fi and Bluetooth
settings for your exact hardware. Do not overwrite your only working bootloader.
The setup tool does not mount, install to or modify your boot partition.

`SHA256SUMS` contains checksums for the distributed archives.

## Snapshot validation

The identity generator was tested with both templates, including the verified
upstream download. All enabled ACPI, kext and driver paths exist. After identity
generation, the pre-patch config passes OpenCore 1.0.8 `ocvalidate`. The current
snapshot reports **16 existing schema/validation issues** against that validator
(missing newer keys and `UEFI/Output/InitialMode`). It is not a cleanly validated
1.0.8 config; resolve version compatibility before deploying. This upload keeps
the owner's existing boot settings rather than silently upgrading them.

Sanitization applies to these downloads, not past Git commits: the previous
archive already published in this repository may remain accessible in history.
