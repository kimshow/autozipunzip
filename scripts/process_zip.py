#!/usr/bin/env python3
"""
ネストしたZIPファイルの処理スクリプト

処理フロー:
1. YYYYMMDD_text.zip を解凍
2. connect/バイナリ/コネクト_vXX.YY.ZZ.zip を解凍
3. aaa.xcframework.zip, bbb.xcframework.zip を解凍
4. 各xcframeworkに署名マーカーを追加
5. 逆順で再圧縮
"""

import shutil
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

# ローカルモジュールのインポート
sys.path.insert(0, str(Path(__file__).parent))
from zip_utils import (
    verify_python_version,
    safe_extract,
    compress_directory,
    add_signature_marker,
    list_zip_contents,
)


def find_zip_files(directory: Path, pattern: str = "*.zip") -> List[Path]:
    """
    ディレクトリ内のZIPファイルを検索

    Args:
        directory: 検索ディレクトリ
        pattern: 検索パターン

    Returns:
        見つかったZIPファイルのリスト
    """
    if directory.is_file():
        return [directory] if directory.suffix == '.zip' else []

    return sorted(directory.glob(pattern))


def process_xcframework_zip(xcfw_zip: Path, work_dir: Path) -> None:
    """
    xcframework.zipを処理（解凍→署名→再圧縮）

    Args:
        xcfw_zip: xcframework.zipファイルのパス
        work_dir: 作業ディレクトリ
    """
    xcfw_name = xcfw_zip.stem  # 'aaa.xcframework' など
    xcfw_dir = work_dir / xcfw_name

    # 1. xcframework.zip を解凍
    safe_extract(xcfw_zip, xcfw_dir)

    # 2. 署名済みマーカーを追加
    print(f"✍️  Adding signature marker to {xcfw_name}")
    add_signature_marker(xcfw_dir)

    # 3. 再圧縮
    compress_directory(xcfw_dir, xcfw_zip, base_path=xcfw_dir)

    # 4. 解凍ディレクトリを削除
    print(f"🗑️  Cleaning up: {xcfw_dir.name}")
    shutil.rmtree(xcfw_dir)
    print()


def process_connect_zip(connect_zip: Path, work_dir: Path) -> None:
    """
    コネクト_vXX.YY.ZZ.zipを処理

    Args:
        connect_zip: コネクトZIPファイルのパス
        work_dir: 作業ディレクトリ
    """
    connect_name = connect_zip.stem
    connect_dir = work_dir / connect_name

    # 1. コネクトZIPを解凍
    safe_extract(connect_zip, connect_dir)

    # 2. ネストした同名ディレクトリを探す
    # 構造: コネクト_vXX.YY.ZZ/コネクト_vXX.YY.ZZ/...
    nested_dir = connect_dir / connect_name

    if not nested_dir.exists():
        print(f"⚠️  Warning: Expected nested directory not found: {nested_dir}")
        print(f"   Available: {list(connect_dir.iterdir())}")
        # 最初のディレクトリを使用
        dirs = [d for d in connect_dir.iterdir() if d.is_dir()]
        if dirs:
            nested_dir = dirs[0]
        else:
            raise FileNotFoundError(f"No directories found in {connect_dir}")

    # 3. xcframework.zipファイルを処理（再帰的に検索）
    xcfw_zips = list(nested_dir.rglob("*.xcframework.zip"))
    print(f"🔍 Found {len(xcfw_zips)} xcframework.zip files")

    for xcfw_zip in xcfw_zips:
        process_xcframework_zip(xcfw_zip, xcfw_zip.parent)

    # 4. コネクトZIPを再圧縮
    compress_directory(connect_dir, connect_zip, base_path=connect_dir)

    # 5. 解凍ディレクトリを削除
    print(f"🗑️  Cleaning up: {connect_dir.name}")
    shutil.rmtree(connect_dir)
    print()


def process_root_zip(
    root_zip: Path,
    output_dir: Path,
    work_dir: Optional[Path] = None
) -> Path:
    """
    ルートZIPファイル（YYYYMMDD_text.zip）を処理

    Args:
        root_zip: 処理するルートZIPファイル
        output_dir: 出力ディレクトリ（signed/）
        work_dir: 作業ディレクトリ（Noneの場合は自動作成）

    Returns:
        出力されたZIPファイルのパス
    """
    print(f"\n{'='*70}")
    print(f"🚀 Processing: {root_zip.name}")
    print(f"{'='*70}\n")

    # 作業ディレクトリの準備
    cleanup_work_dir = False
    if work_dir is None:
        # /tmp直下で作業（パス長対策）
        work_dir = Path(tempfile.mkdtemp(dir='/tmp', prefix='zip_'))
        cleanup_work_dir = True
        print(f"📁 Work directory: {work_dir}\n")

    try:
        root_name = root_zip.stem
        root_dir = work_dir / root_name

        # 1. ルートZIPを解凍
        safe_extract(root_zip, root_dir)

        # 2. connect/バイナリ/ ディレクトリを探す
        connect_dir = root_dir / "connect" / "バイナリ"

        if not connect_dir.exists():
            print(f"⚠️  Warning: Expected path not found: {connect_dir}")
            print(f"   Searching for alternative paths...")
            # connect ディレクトリを探す
            connect_candidates = list(root_dir.glob("**/connect"))
            if connect_candidates:
                # 最初のバイナリディレクトリを探す
                for candidate in connect_candidates:
                    binary_dirs = list(candidate.glob("*バイナリ*"))
                    if binary_dirs:
                        connect_dir = binary_dirs[0]
                        print(f"   ✓ Found: {connect_dir.relative_to(root_dir)}")
                        break

        if not connect_dir.exists():
            raise FileNotFoundError(
                f"Cannot find 'connect/バイナリ' in {root_zip.name}\n"
                f"Available structure:\n{list(root_dir.rglob('*'))[:10]}"
            )

        # 3. コネクトZIPファイルを処理
        connect_zips = find_zip_files(connect_dir, "コネクト_*.zip")
        print(f"🔍 Found {len(connect_zips)} connect ZIP files\n")

        for connect_zip in connect_zips:
            # コネクト_3rd は無視（要件に含まれていない）
            if "3rd" in connect_zip.name:
                print(f"⏭️  Skipping: {connect_zip.name} (3rd party)\n")
                continue

            process_connect_zip(connect_zip, connect_dir)

        # 4. ルートZIPを再圧縮
        output_dir.mkdir(parents=True, exist_ok=True)
        output_zip = output_dir / root_zip.name

        compress_directory(root_dir, output_zip, base_path=root_dir)

        # 5. 解凍ディレクトリを削除
        print(f"🗑️  Cleaning up: {root_dir.name}")
        shutil.rmtree(root_dir)

        print(f"\n{'='*70}")
        print(f"✅ Success: {output_zip.name}")
        print(f"{'='*70}\n")

        return output_zip

    finally:
        # 作業ディレクトリのクリーンアップ
        if cleanup_work_dir and work_dir.exists():
            print(f"🗑️  Cleaning up work directory: {work_dir}")
            shutil.rmtree(work_dir)


def main():
    """メイン処理"""
    verify_python_version()

    # コマンドライン引数の処理
    if len(sys.argv) < 2:
        print("Usage: python process_zip.py <input_zip_or_dir> [output_dir]")
        print()
        print("Examples:")
        print("  python process_zip.py unsign/20260105_text.zip signed/")
        print("  python process_zip.py unsign/ signed/")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("signed")

    if not input_path.exists():
        print(f"❌ Error: Input path not found: {input_path}")
        sys.exit(1)

    # 入力パスの処理
    zip_files = find_zip_files(input_path)

    if not zip_files:
        print(f"❌ Error: No ZIP files found in {input_path}")
        sys.exit(1)

    print(f"\n📦 Found {len(zip_files)} ZIP file(s) to process\n")

    # 各ZIPファイルを処理
    for zip_file in zip_files:
        try:
            output_zip = process_root_zip(zip_file, output_dir)

            # 結果の確認（オプション）
            if output_zip.exists():
                list_zip_contents(output_zip)

        except Exception as e:
            print(f"\n❌ Error processing {zip_file.name}:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

    print("\n✅ All files processed successfully!")


if __name__ == "__main__":
    main()
