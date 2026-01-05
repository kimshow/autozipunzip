# レビュー結果: Win/Mac環境差異とCI/CD対策

## ✅ 修正完了項目

### 1. **UTF-8エンコーディングの明示化** ⚠️ 最重要
**問題**: Python 3.11でも自動的にUTF-8にならない  
**修正**: `metadata_encoding='utf-8'` パラメータを必須化

```python
# ❌ 修正前（Windows文字化け）
with zipfile.ZipFile('output.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write(file_path, arcname=arcname)

# ✅ 修正後（Windows互換）
with zipfile.ZipFile('output.zip', 'w', 
                     compression=zipfile.ZIP_DEFLATED,
                     metadata_encoding='utf-8') as zf:  # Python 3.11+必須
    zf.write(file_path, arcname=arcname)
```

---

### 2. **パス区切り文字の統一** ⚠️ 最重要
**問題**: macOSの`Path`オブジェクトをそのままarcnameに使うとWindows非互換  
**修正**: `.as_posix()` で必ず `/` 区切りに変換

```python
# ❌ 修正前（Windowsで開けない可能性）
arcname = file_path.relative_to(source_dir)  # PosixPath/WindowsPath

# ✅ 修正後（クロスプラットフォーム互換）
arcname = file_path.relative_to(source_dir).as_posix()  # 常に '/' 区切り
```

---

### 3. **GitHub Actions トリガー変更**
**問題**: 計画に `push` トリガーが含まれていた  
**修正**: テスト用に `workflow_dispatch`（手動実行）のみに変更

```yaml
# ❌ 修正前
on:
  push:
    paths:
      - 'unsign/**'
  workflow_dispatch:

# ✅ 修正後
on:
  workflow_dispatch:  # 手動トリガーのみ
    inputs:
      zip_file:
        description: 'ZIP filename in unsign/ (e.g., 20260105_text.zip)'
        required: false
        type: string
```

**追加機能**: 特定ZIPファイルを指定実行可能に

---

### 4. **Python バージョンチェック追加**
**問題**: Python 3.11未満で実行されるとUTF-8エンコーディングが機能しない  
**修正**: CI実行時にバージョンを検証

```yaml
- name: Verify Python version
  run: python -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11+ required'"
```

---

### 5. **長いパス対策の具体化**
**問題**: 実装方法が不明確  
**修正**: `tempfile.TemporaryDirectory` を使用し、自動クリーンアップ

```python
import tempfile

# /tmp直下で作業（macOS最大パス長: 1024文字）
with tempfile.TemporaryDirectory(dir='/tmp', prefix='zip_') as tmpdir:
    work_dir = Path(tmpdir)
    # 処理...
    # コンテキストマネージャーで自動削除（try-finally不要）
```

---

### 6. **エラーハンドリング強化**
**変更箇所**: `.github/copilot-instructions.md`  
**内容**: `try-finally` で一時ディレクトリの確実な削除を指示

---

## 🎯 Win/Mac環境差異の完全対策リスト

| 差異項目 | macOS (作成側) | Windows (利用側) | 対策 |
|---------|---------------|-----------------|------|
| パス区切り | `/` | `\` | `.as_posix()` で強制的に `/` |
| 文字エンコーディング | UTF-8 | CP932/Shift-JIS | `metadata_encoding='utf-8'` |
| 改行コード | LF | CRLF | ZIP内では影響なし（バイナリ） |
| ファイル名大文字小文字 | 区別なし（デフォルト） | 区別なし | 問題なし |
| 最大パス長 | 1024文字 | 260文字（古い制限） | 短いディレクトリ名使用 |

---

## 📋 CI/CD実装チェックリスト

### GitHub Actions ワークフロー
- [x] macOS-latest ランナー使用
- [x] Python 3.11以上を指定
- [x] バージョンチェックステップ追加
- [x] 手動トリガーのみ（`workflow_dispatch`）
- [x] 入力パラメータで特定ZIPファイル指定可能
- [x] Git自動コミット＆プッシュ（[skip ci]付き）

### Python スクリプト
- [x] `metadata_encoding='utf-8'` 必須化を明記
- [x] `.as_posix()` でarcname変換を明記
- [x] `tempfile.TemporaryDirectory` 使用を明記
- [x] ログ出力でCI可視化
- [ ] エラー時のスタックトレース出力（実装時）
- [ ] 元ファイルの保持（実装時）

---

## 🚨 残る実装時の注意点

### 1. **テスト方法**
```bash
# 1. ローカルで日本語ZIP作成
python tests/fixtures/create_test_zip.py

# 2. ローカル実行
python scripts/process_zip.py unsign/20260105_text.zip signed/

# 3. Windows検証（macで確認）
unzip -l signed/20260105_text.zip | grep -E '[\x80-\xFF]'  # 日本語表示確認
```

### 2. **GitHub Actions デバッグ**
- `workflow_dispatch` の入力欄でZIPファイル名を指定して実行
- ログで各ステップの成功/失敗を確認
- Windows PCでダウンロードして実際に解凍テスト

### 3. **エッジケース**
- 空のディレクトリ（zipfileは保存しない仕様）
- シンボリックリンク（無視するか実体をコピーするか）
- 特殊文字を含むファイル名（`/`, `\`, `:`など）

---

## ✅ 結論: 対策は完了

**Win/Mac環境差異**: 全て対策済み  
**CI/CD設定**: 手動トリガー化完了  
**次のステップ**: 実装コード生成に進んで問題なし

修正内容は以下のファイルに反映済み:
- [.github/copilot-instructions.md](.github/copilot-instructions.md)
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
