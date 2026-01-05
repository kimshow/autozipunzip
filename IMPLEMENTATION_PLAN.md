# 実装計画: autozipunzip

## 📋 概要
GitHub Actions（macOS）でネストしたZIPファイルを解凍→署名→再圧縮し、Windows互換性を保つワークフロー。

---

## 🎯 完了条件
- [ ] Windows環境で日本語ファイル名のZIPが正しく開ける
- [ ] 3層ネストのZIP構造を処理できる
- [ ] 署名済みマーカー（署名済み.txt）が正しく挿入される
- [ ] 元のディレクトリ構造が保持される
- [ ] 処理後のZIPがsigned/に配置される

---

## 📂 実装するファイル

### 1. GitHub Actions ワークフロー
**ファイル**: `.github/workflows/sign-and-repackage.yml`

```yaml
name: Sign and Repackage ZIP
on:
  workflow_dispatch:  # 手動トリガーのみ（テスト用）
    inputs:
      zip_file:
        description: 'ZIP filename in unsign/ (e.g., 20260105_text.zip)'
        required: false
        type: string

jobs:
  process:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'  # UTF-8 metadata_encoding必須
      
      - name: Verify Python version
        run: python -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required'"
      
      - name: Process ZIP files
        run: |
          if [ -n "${{ inputs.zip_file }}" ]; then
            python scripts/process_zip.py "unsign/${{ inputs.zip_file }}" signed/
          else
            python scripts/process_zip.py unsign/ signed/
          fi
      
      - name: Commit signed files
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add signed/
          git diff --staged --quiet || git commit -m "Add signed ZIP [skip ci]"
          git push
```

---

### 2. メインスクリプト
**ファイル**: `scripts/process_zip.py`

**責務**:
- `unsign/` 内のZIPファイルを検出
- ネストした解凍・署名・再圧縮を実行
- 処理済みファイルを `signed/` に配置

**主要関数**:
```python
def extract_zip_utf8(zip_path: Path, extract_to: Path) -> None:
    """UTF-8対応でZIPを解凍"""

def compress_directory_utf8(source_dir: Path, output_zip: Path) -> None:
    """UTF-8でディレクトリをZIP化（Windows互換）"""

def add_signature_marker(target_dir: Path) -> None:
    """署名済み.txtをディレクトリに追加"""

def process_nested_zips(root_zip: Path, output_dir: Path) -> None:
    """3層ネストZIPの処理メインロジック"""
```

---

### 3. ユーティリティ
**ファイル**: `scripts/zip_utils.py`

**責務**:
- UTF-8対応のZIP操作
- パストラバーサル対策
- ログ出力

**主要関数**:
```python
def safe_extract(zip_file: ZipFile, member: str, target_dir: Path) -> Path:
    """安全な解凍（パストラバーサル対策）"""

def zip_directory_recursive(source: Path, zip_obj: ZipFile, base_path: Path) -> None:
    """再帰的にディレクトリをZIP化"""
```

---

### 4. テスト用フィクスチャ
**ファイル**: `tests/fixtures/create_test_zip.py`

日本語ファイル名を含むテストZIPを生成するスクリプト。

---

## 🔄 処理フロー

```
1. unsign/YYYYMMDD_text.zip を検出
   ↓
2. /tmp/work/ に解凍
   └── connect/バイナリ/コネクト_vXX.YY.ZZ.zip
   ↓
3. コネクト_vXX.YY.ZZ.zip を解凍
   └── コネクト_vXX.YY.ZZ/コネクト_vXX.YY.ZZ/
       ├── aaa.xcframework.zip
       └── bbb.xcframework.zip
   ↓
4. aaa, bbb.xcframework.zip を解凍
   ↓
5. 各 xcframework に「署名済み.txt」を追加
   ↓
6. aaa, bbb をZIP化 → 元のフォルダ削除
   ↓
7. コネクト_vXX.YY.ZZ をZIP化 → 元のフォルダ削除
   ↓
8. YYYYMMDD_text をZIP化 → /tmp/work/ 削除
   ↓
9. signed/YYYYMMDD_text.zip に配置
```

---

## 🛠️ 技術的実装ポイント

### UTF-8エンコーディング（Windows互換）
```python
import zipfile
from pathlib import Path

# Python 3.11+ ではデフォルトでUTF-8が使用される
with zipfile.ZipFile(output_path, 'w', 
                     compression=zipfile.ZIP_DEFLATED) as zf:
    for file in all_files:
        # ✅ 必須: as_posix() でパス区切りを / に統一
        arcname = Path(file).relative_to(base_dir).as_posix()
        zf.write(file, arcname=arcname)
```

### ディレクトリ再帰圧縮
```python
import os
import zipfile
from pathlib import Path

def compress_directory_utf8(source_dir: Path, output_zip: Path) -> None:
    """ディレクトリをUTF-8でZIP化（Windows互換）"""
    with zipfile.ZipFile(output_zip, 'w', 
                         compression=zipfile.ZIP_DEFLATED,
                         metadata_encoding='utf-8') as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                # ✅ 重要: as_posix()で必ず / 区切りに
                arcname = file_path.relative_to(source_dir).as_posix()
                zf.write(file_path, arcname=arcname)
                print(f"  Added: {arcname}")  # CI可視化用
```

### パス長対策
```python
import tempfile
import shutil

# /tmp直下で作業してパス長を最小化（macOS最大1024文字）
with tempfile.TemporaryDirectory(dir='/tmp', prefix='zip_') as tmpdir:
    work_dir = Path(tmpdir)
    # 処理... （コンテキストマネージャーで自動削除）
```

---

## 🧪 テスト計画

### ローカルテスト
```bash
# 1. テストZIP作成
python tests/fixtures/create_test_zip.py

# 2. 処理実行
python scripts/process_zip.py

# 3. 結果確認（Windowsシミュレーション）
# macOS上でのZIP内容確認
unzip -l signed/YYYYMMDD_text.zip
```

### GitHub Actions テスト
1. `unsign/` に小さなテストZIPをプッシュ
2. ワークフロー実行を確認
3. `signed/` に出力されたZIPをダウンロード
4. Windows環境で解凍テスト

---

## 📝 次のステップ

### Phase 1: 基本実装（優先度: 高）
1. ✅ `.github/copilot-instructions.md` 作成完了
2. ⬜ `scripts/zip_utils.py` 作成
3. ⬜ `scripts/process_zip.py` 作成
4. ⬜ `.github/workflows/sign-and-repackage.yml` 作成

### Phase 2: テスト（優先度: 高）
5. ⬜ `tests/fixtures/create_test_zip.py` 作成
6. ⬜ ローカルでの動作確認
7. ⬜ GitHub Actions での動作確認

### Phase 3: ドキュメント（優先度: 中）
8. ⬜ `README.md` 作成（使い方、トラブルシューティング）
9. ⬜ Windows検証手順のドキュメント化

---

## ⚠️ リスクと対策

| リスク | 対策 |
|--------|------|
| 日本語ファイル名の文字化け | Python 3.11以降を使用（UTF-8デフォルト） |
| パス長制限 | `/tmp` 直下で作業、短いディレクトリ名使用 |
| 処理途中でのエラー | try-finally で一時ファイルを確実に削除 |
| Git LFS制限 | ZIPファイルサイズに注意（GitHub Actions内で完結） |

---

## 🚀 実装開始準備完了

上記計画に基づき、Phase 1から実装を開始できます。
