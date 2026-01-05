#!/usr/bin/env python3
"""
ZIPファイルの詳細診断 - Windows互換性の問題を特定

使用方法:
    python tests/diagnose_zip.py signed/20260105_test.zip
"""

import os
import sys
import struct
import zipfile
from pathlib import Path


def read_zip_headers(zip_path: Path):
    """ZIPファイルのヘッダー情報を詳細に読み取る"""
    print(f"\n{'='*70}")
    print(f"📋 RAW ZIP HEADER ANALYSIS: {zip_path.name}")
    print(f"{'='*70}\n")

    with open(zip_path, "rb") as f:
        # ファイルサイズ
        f.seek(0, 2)
        file_size = f.tell()
        f.seek(0)

        print(f"File size: {file_size:,} bytes ({file_size/1024:.2f} KB)\n")

        # 最初の4バイト（シグネチャ）
        signature = f.read(4)
        print(f"Signature: 0x{signature.hex()} ({signature})")

        if signature == b"PK\x03\x04":
            print("  ✅ Valid Local File Header")
        elif signature == b"PK\x01\x02":
            print("  ⚠️  Central Directory Header (unusual at start)")
        elif signature == b"PK\x05\x06":
            print("  ⚠️  End of Central Directory (unusual at start)")
        else:
            print("  ❌ Invalid ZIP signature!")
            return

        # Local File Header の詳細読み取り
        f.seek(0)
        lfh_data = f.read(30)  # Local File Header は最低30バイト

        if len(lfh_data) >= 30:
            # バージョン
            version = struct.unpack("<H", lfh_data[4:6])[0]
            print(f"\nVersion needed: {version // 10}.{version % 10}")

            # 汎用ビットフラグ
            flags = struct.unpack("<H", lfh_data[6:8])[0]
            print(f"\nGeneral purpose bit flags: 0b{flags:016b} (0x{flags:04x})")
            print(f"  Bit 0 (encrypted):     {bool(flags & 0x0001)}")
            print(f"  Bit 3 (data desc):     {bool(flags & 0x0008)}")
            print(f"  Bit 11 (UTF-8):        {bool(flags & 0x0800)} {'✅' if flags & 0x0800 else '❌ PROBLEM!'}")

            # 圧縮方法
            compression = struct.unpack("<H", lfh_data[8:10])[0]
            compression_name = {0: "STORED (no compression)", 8: "DEFLATED"}.get(
                compression, f"Unknown ({compression})"
            )
            print(f"\nCompression method: {compression} ({compression_name})")

            # ファイル名長
            filename_len = struct.unpack("<H", lfh_data[26:28])[0]
            extra_len = struct.unpack("<H", lfh_data[28:30])[0]
            print(f"\nFilename length: {filename_len} bytes")
            print(f"Extra field length: {extra_len} bytes")

            # ファイル名を読み取る
            filename_bytes = f.read(filename_len)
            print(f"\nFilename (raw bytes): {filename_bytes.hex()}")
            try:
                filename_utf8 = filename_bytes.decode("utf-8")
                print(f"Filename (UTF-8): {filename_utf8}")
            except:
                print(f"Filename (UTF-8): ❌ DECODE ERROR")

            try:
                filename_cp437 = filename_bytes.decode("cp437")
                print(f"Filename (CP437): {filename_cp437}")
            except:
                print(f"Filename (CP437): ❌ DECODE ERROR")


def analyze_with_zipfile(zip_path: Path):
    """zipfileモジュールで解析"""
    print(f"\n{'='*70}")
    print(f"🔍 ZIPFILE MODULE ANALYSIS")
    print(f"{'='*70}\n")

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # 整合性チェック
            bad = zf.testzip()
            if bad:
                print(f"❌ Corrupted file detected: {bad}")
            else:
                print("✅ ZIP integrity: OK")

            print(f"\nTotal entries: {len(zf.namelist())}")

            # 各エントリの詳細
            for idx, info in enumerate(zf.infolist(), 1):
                print(f"\n--- Entry #{idx} ---")
                print(f"Filename: {info.filename}")
                print(f"  Filename bytes: {info.filename.encode('utf-8').hex()}")
                print(f"  Compressed size: {info.compress_size:,} bytes")
                print(f"  Uncompressed size: {info.file_size:,} bytes")
                print(
                    f"  Compress type: {info.compress_type} ({['STORED', '', '', '', '', '', '', '', 'DEFLATED'][info.compress_type] if info.compress_type < 9 else 'UNKNOWN'})"
                )
                print(f"  Flag bits: 0b{info.flag_bits:016b} (0x{info.flag_bits:04x})")
                print(
                    f"    UTF-8 flag (bit 11): {bool(info.flag_bits & 0x800)} {'✅' if info.flag_bits & 0x800 else '❌'}"
                )
                print(f"  CRC-32: 0x{info.CRC:08x}")
                print(f"  External attr: 0x{info.external_attr:08x}")

                # ファイルが実際に読み取れるか
                try:
                    data = zf.read(info.filename)
                    print(f"  Read test: ✅ OK ({len(data)} bytes)")
                except Exception as e:
                    print(f"  Read test: ❌ ERROR - {e}")

    except Exception as e:
        print(f"❌ Error opening ZIP: {e}")
        import traceback

        traceback.print_exc()


def check_windows_compatibility(zip_path: Path):
    """Windows互換性のチェック"""
    print(f"\n{'='*70}")
    print(f"🪟 WINDOWS COMPATIBILITY CHECK")
    print(f"{'='*70}\n")

    issues = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            filename = info.filename

            # 1. パスの長さチェック（Windows MAX_PATH = 260）
            if len(filename) > 200:
                issues.append(f"⚠️  Long path ({len(filename)} chars): {filename}")

            # 2. 予約語チェック
            reserved = [
                "CON",
                "PRN",
                "AUX",
                "NUL",
                "COM1",
                "COM2",
                "COM3",
                "COM4",
                "COM5",
                "COM6",
                "COM7",
                "COM8",
                "COM9",
                "LPT1",
                "LPT2",
                "LPT3",
                "LPT4",
                "LPT5",
                "LPT6",
                "LPT7",
                "LPT8",
                "LPT9",
            ]
            parts = filename.split("/")
            for part in parts:
                name_only = part.split(".")[0].upper()
                if name_only in reserved:
                    issues.append(f"⚠️  Reserved name: {filename}")

            # 3. 禁止文字チェック（Windows）
            forbidden = ["<", ">", ":", '"', "|", "?", "*"]
            for char in forbidden:
                if char in filename:
                    issues.append(f"⚠️  Forbidden char '{char}': {filename}")

            # 4. UTF-8フラグチェック
            if not (info.flag_bits & 0x800):
                # 日本語が含まれているか
                try:
                    filename.encode("ascii")
                except UnicodeEncodeError:
                    issues.append(f"❌ Non-ASCII without UTF-8 flag: {filename}")

    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✅ No Windows compatibility issues detected")


def main():
    if len(sys.argv) < 2:
        print("Usage: python tests/diagnose_zip.py <zip_file>")
        print()
        print("Example:")
        print("  python tests/diagnose_zip.py signed/20260105_test.zip")
        sys.exit(1)

    zip_path = Path(sys.argv[1])
    if not zip_path.exists():
        print(f"❌ File not found: {zip_path}")
        sys.exit(1)

    print(f"\n{'#'*70}")
    print(f"# ZIP DIAGNOSTIC REPORT")
    print(f"# File: {zip_path}")
    print(f"# Python: {sys.version}")
    print(f"{'#'*70}")

    # 1. バイナリレベルの解析
    read_zip_headers(zip_path)

    # 2. zipfileモジュールでの解析
    analyze_with_zipfile(zip_path)

    # 3. Windows互換性チェック
    check_windows_compatibility(zip_path)

    print(f"\n{'#'*70}")
    print(f"# DIAGNOSIS COMPLETE")
    print(f"{'#'*70}\n")


if __name__ == "__main__":
    main()
