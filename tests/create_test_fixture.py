#!/usr/bin/env python3
"""
テスト用のネストしたZIPファイルを作成

使用方法:
    python tests/create_test_fixture.py
"""

import os
import sys
import zipfile
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from zip_utils import verify_python_version


def create_test_zip(output_dir: Path = Path("unsign")):
    """
    テスト用のZIPファイルを作成

    構造:
    20260105_test.zip
    └── connect/
        └── バイナリ/
            └── コネクト_v1.0.0.zip
                └── コネクト_v1.0.0/
                    └── コネクト_v1.0.0/
                        ├── aaa.xcframework.zip
                        │   └── aaa.xcframework/
                        │       ├── Info.plist
                        │       └── ios-arm64/
                        │           └── aaa.framework/
                        │               └── aaa
                        └── bbb.xcframework.zip
                            └── bbb.xcframework/
                                ├── Info.plist
                                └── ios-arm64/
                                    └── bbb.framework/
                                        └── bbb
    """
    verify_python_version()

    print("🔨 Creating test ZIP fixture with Japanese filenames...")
    print()

    # 出力ディレクトリを作成
    output_dir.mkdir(parents=True, exist_ok=True)

    # 作業ディレクトリ
    work_dir = Path("tests/temp_fixture")
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1. xcframeworkの構造を作成
        for framework_name in ["aaa", "bbb"]:
            framework_dir = work_dir / f"{framework_name}.xcframework"
            framework_dir.mkdir(parents=True, exist_ok=True)

            # Info.plist
            info_plist = framework_dir / "Info.plist"
            info_plist.write_text(
                f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<plist version="1.0">\n'
                f'<dict>\n'
                f'    <key>CFBundleIdentifier</key>\n'
                f'    <string>com.example.{framework_name}</string>\n'
                f'</dict>\n'
                f'</plist>\n',
                encoding='utf-8'
            )

            # フレームワークバイナリ
            binary_dir = framework_dir / "ios-arm64" / f"{framework_name}.framework"
            binary_dir.mkdir(parents=True, exist_ok=True)
            binary_file = binary_dir / framework_name
            binary_file.write_bytes(b'\x00' * 1024)  # ダミーバイナリ

            print(f"✓ Created {framework_name}.xcframework/")

        # 2. xcframework.zipファイルを作成
        connect_nested_dir = work_dir / "コネクト_v1.0.0" / "コネクト_v1.0.0"
        connect_nested_dir.mkdir(parents=True, exist_ok=True)

        for framework_name in ["aaa", "bbb"]:
            xcfw_zip = connect_nested_dir / f"{framework_name}.xcframework.zip"
            xcfw_dir = work_dir / f"{framework_name}.xcframework"

            with zipfile.ZipFile(
                xcfw_zip, 'w',
                compression=zipfile.ZIP_DEFLATED
            ) as zf:
                for root, dirs, files in os.walk(xcfw_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(work_dir).as_posix()
                        zf.write(file_path, arcname=arcname)

            print(f"✓ Created {framework_name}.xcframework.zip")

        # xcframeworkディレクトリを削除
        for framework_name in ["aaa", "bbb"]:
            import shutil
            shutil.rmtree(work_dir / f"{framework_name}.xcframework")

        # 3. コネクトZIPを作成
        connect_zip_path = work_dir / "connect" / "バイナリ" / "コネクト_v1.0.0.zip"
        connect_zip_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(
            connect_zip_path, 'w',
            compression=zipfile.ZIP_DEFLATED
        ) as zf:
            connect_source = work_dir / "コネクト_v1.0.0"
            for root, dirs, files in os.walk(connect_source):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(work_dir).as_posix()
                    zf.write(file_path, arcname=arcname)

        print(f"✓ Created コネクト_v1.0.0.zip")

        # コネクトディレクトリを削除
        import shutil
        shutil.rmtree(work_dir / "コネクト_v1.0.0")

        # 4. ルートZIPを作成
        root_zip_path = output_dir / "20260105_test.zip"

        with zipfile.ZipFile(
            root_zip_path, 'w',
            compression=zipfile.ZIP_DEFLATED
        ) as zf:
            connect_source = work_dir / "connect"
            for root, dirs, files in os.walk(connect_source):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(work_dir).as_posix()
                    zf.write(file_path, arcname=arcname)

        print(f"✓ Created 20260105_test.zip")
        print()

        # ファイルサイズを表示
        size_kb = root_zip_path.stat().st_size / 1024
        print(f"✅ Test fixture created: {root_zip_path} ({size_kb:.1f} KB)")
        print()
        print("📋 ZIP structure:")
        with zipfile.ZipFile(root_zip_path, 'r') as zf:
            for name in zf.namelist():
                print(f"   {name}")
        print()
        print("🚀 Run test:")
        print(f"   python scripts/process_zip.py {root_zip_path} signed/")

    finally:
        # クリーンアップ
        import shutil
        if work_dir.exists():
            shutil.rmtree(work_dir)


if __name__ == "__main__":
    create_test_zip()
