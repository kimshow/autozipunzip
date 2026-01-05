#!/usr/bin/env python3
"""
ZIPファイルの完全性とWindows互換性を検証

使用方法:
    python tests/verify_zip.py signed/20260105_test.zip
"""

import sys
import zipfile
from pathlib import Path


def verify_zip_file(zip_path: Path) -> bool:
    """ZIPファイルの完全性とWindows互換性を検証"""
    print(f"🔍 Verifying: {zip_path}")
    print("=" * 60)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # 1. 整合性チェック
            print("\n1. Integrity check...")
            bad_files = zf.testzip()
            if bad_files:
                print(f"   ❌ Corrupted: {bad_files}")
                return False
            print("   ✅ ZIP integrity OK")
            
            # 2. マジックバイト確認
            print("\n2. Magic bytes check...")
            zf.fp.seek(0)
            magic = zf.fp.read(4)
            expected = b'PK\x03\x04'
            if magic == expected:
                print(f"   ✅ Magic bytes OK: {magic.hex()}")
            else:
                print(f"   ❌ Invalid magic: {magic.hex()} (expected: {expected.hex()})")
                return False
            
            # 3. エントリ詳細
            print(f"\n3. Entries ({len(zf.infolist())} total)...")
            for info in zf.infolist():
                utf8_flag = "UTF-8" if (info.flag_bits & 0x800) else "NO-UTF8"
                compress_name = {
                    0: "STORED",
                    8: "DEFLATED"
                }.get(info.compress_type, f"TYPE-{info.compress_type}")
                
                # ディレクトリかファイルか
                is_dir = info.filename.endswith('/')
                entry_type = "[DIR]" if is_dir else "[FILE]"
                
                print(f"   {entry_type} {info.filename:50} [{utf8_flag}] [{compress_name}]")
            
            # 4. ファイルサイズ
            print(f"\n4. File size...")
            file_size = zip_path.stat().st_size
            print(f"   {file_size:,} bytes ({file_size / 1024:.2f} KB)")
            
            print("\n" + "=" * 60)
            print("✅ All checks passed!")
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tests/verify_zip.py <zip_file>")
        print()
        print("Example:")
        print("  python tests/verify_zip.py signed/20260105_test.zip")
        sys.exit(1)
    
    zip_path = Path(sys.argv[1])
    if not zip_path.exists():
        print(f"❌ File not found: {zip_path}")
        sys.exit(1)
    
    success = verify_zip_file(zip_path)
    sys.exit(0 if success else 1)
