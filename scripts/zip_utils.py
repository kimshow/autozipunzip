"""
ZIP操作ユーティリティ - UTF-8対応とWindows互換性

このモジュールはmacOS上で作成したZIPファイルが
Windows環境で日本語ファイル名を正しく表示できるようにします。
"""

import os
import sys
import zipfile
from pathlib import Path
from typing import Optional


def verify_python_version() -> None:
    """Python 3.11以上であることを確認（UTF-8 metadata_encoding必須）"""
    if sys.version_info < (3, 11):
        raise RuntimeError(
            f"Python 3.11+ required for UTF-8 ZIP support. "
            f"Current version: {sys.version_info.major}.{sys.version_info.minor}"
        )


def safe_extract(zip_path: Path, extract_to: Path) -> None:
    """
    ZIPファイルを安全に解凍（パストラバーサル対策付き）

    Args:
        zip_path: 解凍するZIPファイルのパス
        extract_to: 解凍先ディレクトリ

    Raises:
        ValueError: パストラバーサル攻撃を検出した場合
    """
    extract_to = extract_to.resolve()
    extract_to.mkdir(parents=True, exist_ok=True)

    print(f"📦 Extracting: {zip_path.name}")
    print(f"   → {extract_to}")

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            # パストラバーサル対策
            member_path = (extract_to / member).resolve()
            if not str(member_path).startswith(str(extract_to)):
                raise ValueError(
                    f"Path traversal detected: {member} -> {member_path}"
                )

            # 解凍実行
            zf.extract(member, extract_to)
            print(f"   ✓ {member}")

    print(f"   ✅ Extracted {len(zf.namelist())} files\n")


def compress_directory(
    source_dir: Path,
    output_zip: Path,
    base_path: Optional[Path] = None
) -> None:
    """
    ディレクトリを再帰的にZIP圧縮（UTF-8エンコーディング、Windows互換）

    Args:
        source_dir: 圧縮するディレクトリ
        output_zip: 出力ZIPファイルのパス
        base_path: アーカイブ名の基準パス（Noneの場合はsource_dir）

    Example:
        compress_directory(Path('/tmp/mydir'), Path('output.zip'))
        # mydir内のファイルがZIPのルートに配置される
    """
    source_dir = source_dir.resolve()
    output_zip.parent.mkdir(parents=True, exist_ok=True)

    if base_path is None:
        base_path = source_dir
    else:
        base_path = base_path.resolve()

    print(f"📦 Compressing: {source_dir.name}")
    print(f"   → {output_zip.name}")

    file_count = 0

    # UTF-8エンコーディングでZIP作成（Windows互換の鍵）
    # Python 3.11+ではデフォルトでUTF-8が使用される
    with zipfile.ZipFile(
        output_zip,
        'w',
        compression=zipfile.ZIP_DEFLATED
    ) as zf:
        # ディレクトリを再帰的に走査
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file

                # 相対パスを計算し、POSIX形式（/区切り）に変換
                # これによりWindowsでも正しく開ける
                arcname = file_path.relative_to(base_path).as_posix()

                zf.write(file_path, arcname=arcname)
                print(f"   ✓ {arcname}")
                file_count += 1

    # 圧縮結果の確認
    zip_size_mb = output_zip.stat().st_size / (1024 * 1024)
    print(f"   ✅ Compressed {file_count} files ({zip_size_mb:.2f} MB)\n")


def add_signature_marker(target_dir: Path, marker_filename: str = "署名済み.txt") -> None:
    """
    署名済みマーカーファイルを追加

    Args:
        target_dir: マーカーを追加するディレクトリ
        marker_filename: マーカーファイル名
    """
    marker_file = target_dir / marker_filename
    marker_file.write_text(
        f"このフレームワークは署名済みです\n"
        f"Signed at: {marker_file}\n",
        encoding='utf-8'
    )
    print(f"   ✓ Added signature marker: {marker_filename}")


def list_zip_contents(zip_path: Path) -> None:
    """
    ZIPファイルの内容を表示（デバッグ用）

    Args:
        zip_path: 表示するZIPファイル
    """
    print(f"\n📋 Contents of {zip_path.name}:")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for info in zf.infolist():
            size_kb = info.file_size / 1024
            print(f"   {info.filename:60} ({size_kb:>8.1f} KB)")
    print()
