#!/usr/bin/env python3
"""
Windows互換性の参照用ZIPを複数の方法で生成
どの方法がWindowsで動作するかを比較検証
"""

import zipfile
import subprocess
from pathlib import Path
import tempfile
import shutil


def create_test_structure():
    """テスト用のディレクトリ構造を作成"""
    tmp = Path(tempfile.mkdtemp(prefix="ziptest_"))
    test_dir = tmp / "テストフォルダ"
    sub_dir = test_dir / "サブフォルダ"
    sub_dir.mkdir(parents=True)
    
    (test_dir / "test1.txt").write_text("Test file 1\n", encoding="utf-8")
    (sub_dir / "日本語ファイル.txt").write_text("Japanese filename test\n", encoding="utf-8")
    
    return tmp, test_dir


def method1_python_default(test_dir: Path, output: Path):
    """方法1: Python標準のwrite()メソッド"""
    print("Method 1: Python zipfile.write()")
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in test_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(test_dir.parent).as_posix()
                zf.write(file, arcname)
    print(f"  → {output}")


def method2_python_utf8_flag(test_dir: Path, output: Path):
    """方法2: Python + 明示的UTF-8フラグ（現在の実装）"""
    print("Method 2: Python with explicit UTF-8 flag")
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file in test_dir.rglob("*"):
            if file.is_file():
                arcname = file.relative_to(test_dir.parent).as_posix()
                zip_info = zipfile.ZipInfo.from_file(file, arcname)
                zip_info.flag_bits |= 0x800
                with open(file, 'rb') as f:
                    zf.writestr(zip_info, f.read())
    print(f"  → {output}")


def method3_system_zip(test_dir: Path, output: Path):
    """方法3: システムのzipコマンド"""
    print("Method 3: System zip command")
    try:
        # macOSのzipコマンドは-UN=UTF8オプションでUTF-8対応
        subprocess.run(
            ['zip', '-r', '-UN=UTF8', str(output), test_dir.name],
            cwd=test_dir.parent,
            check=True,
            capture_output=True
        )
        print(f"  → {output}")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed: {e.stderr.decode()}")
    except FileNotFoundError:
        print("  ✗ zip command not found")


def method4_ditto(test_dir: Path, output: Path):
    """方法4: macOSのditto（Apple推奨）"""
    print("Method 4: macOS ditto command")
    try:
        subprocess.run(
            ['ditto', '-c', '-k', '--sequesterRsrc', '--keepParent',
             str(test_dir), str(output)],
            check=True,
            capture_output=True
        )
        print(f"  → {output}")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Failed: {e.stderr.decode()}")
    except FileNotFoundError:
        print("  ✗ ditto command not found")


def analyze_zip(zip_path: Path):
    """生成されたZIPを分析"""
    print(f"\nAnalyzing: {zip_path.name}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            print(f"  Entries: {len(zf.namelist())}")
            for info in zf.infolist():
                utf8_flag = bool(info.flag_bits & 0x800)
                print(f"    {info.filename:40} UTF-8={utf8_flag}")
    except Exception as e:
        print(f"  ✗ Error: {e}")


def main():
    """メイン処理"""
    print("=" * 70)
    print("Windows互換性テスト用ZIP生成")
    print("=" * 70)
    
    tmp, test_dir = create_test_structure()
    output_dir = Path(__file__).parent.parent / "tests" / "reference_zips"
    output_dir.mkdir(exist_ok=True)
    
    try:
        # 各方法でZIP生成
        methods = [
            (method1_python_default, "method1_default.zip"),
            (method2_python_utf8_flag, "method2_utf8flag.zip"),
            (method3_system_zip, "method3_systemzip.zip"),
            (method4_ditto, "method4_ditto.zip"),
        ]
        
        for method_func, filename in methods:
            output = output_dir / filename
            try:
                method_func(test_dir, output)
            except Exception as e:
                print(f"  ✗ Exception: {e}")
        
        print("\n" + "=" * 70)
        print("生成されたZIPファイルの分析")
        print("=" * 70)
        
        for _, filename in methods:
            zip_path = output_dir / filename
            if zip_path.exists():
                analyze_zip(zip_path)
        
        print("\n" + "=" * 70)
        print("✅ 完了")
        print(f"生成場所: {output_dir}")
        print("\nWindows環境でこれらのZIPファイルを解凍テストしてください")
        print("=" * 70)
        
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    main()
