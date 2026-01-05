# autozipunzip

GitHub Actions上でネストしたZIPファイルを解凍→署名→再圧縮し、Windows互換性を保つ自動化ツール。

## 🎯 目的

macOSランナー上で日本語ファイル名を含むZIPファイルを処理し、Windows環境でも正しく開けるようUTF-8エンコーディングで再圧縮します。

## 📂 ディレクトリ構造

```
/
├── unsign/           # 入力: 未署名ZIPファイル
├── signed/           # 出力: 署名済み再圧縮ZIPファイル
├── .github/
│   └── workflows/    # GitHub Actionsワークフロー
└── scripts/          # Python処理スクリプト
```

## 🚀 使い方

### GitHub Actionsで実行（推奨）

1. **ZIPファイルを準備**
   ```bash
   # unsign/ ディレクトリにZIPファイルを配置
   cp /path/to/YYYYMMDD_text.zip unsign/
   git add unsign/
   git commit -m "Add ZIP file to process"
   git push
   ```

2. **手動でワークフローを実行**
   - GitHubリポジトリの「Actions」タブを開く
   - 「Sign and Repackage ZIP」ワークフローを選択
   - 「Run workflow」をクリック
   - （オプション）特定のZIPファイル名を入力
   - 「Run workflow」で実行

3. **結果を確認**
   - ワークフロー完了後、`signed/` ディレクトリに署名済みZIPが配置される
   - Artifactsからもダウンロード可能

### ローカル実行

```bash
# Python 3.11以上が必要
python3 --version  # 3.11+ であることを確認

# 特定のZIPファイルを処理
python scripts/process_zip.py unsign/20260105_text.zip signed/

# unsign/ 内の全ZIPファイルを処理
python scripts/process_zip.py unsign/ signed/
```

## 📦 処理対象のファイル構造

```
YYYYMMDD_text.zip
└── connect/
    └── バイナリ/
        ├── コネクト_vXX.YY.ZZ.zip
        │   └── コネクト_vXX.YY.ZZ/
        │       └── コネクト_vXX.YY.ZZ/
        │           ├── aaa.xcframework.zip
        │           └── bbb.xcframework.zip
        └── コネクト_3rd_vXX.YY.ZZ.zip (処理対象外)
```

## 🔄 処理フロー

1. `YYYYMMDD_text.zip` を解凍
2. `connect/バイナリ/コネクト_vXX.YY.ZZ.zip` を解凍
3. `aaa.xcframework.zip`, `bbb.xcframework.zip` を解凍
4. 各xcframeworkに「署名済み.txt」マーカーを追加
5. xcframeworkをZIP化 → 元のフォルダ削除
6. コネクトZIPを再圧縮 → 元のフォルダ削除
7. ルートZIPを再圧縮 → 作業ディレクトリ削除
8. `signed/` に出力

## ✅ Windows互換性の保証

### UTF-8エンコーディング

```python
# Python 3.11+ はデフォルトでUTF-8を使用
with zipfile.ZipFile('output.zip', 'w', 
                     compression=zipfile.ZIP_DEFLATED) as zf:
    # arcnameは.as_posix()でPOSIX形式に変換（Windows互換）
    arcname = file_path.relative_to(base).as_posix()
    zf.write(file_path, arcname=arcname)
```

### パス区切り文字の統一

```python
# 常に '/' 区切りに変換（Windows互換）
arcname = file_path.relative_to(base).as_posix()
```

## 🧪 テスト

### Windows環境での確認方法

**⚠️ 重要：GitHubの「Download ZIP」ではなく、`git clone`を使用してください**

GitHubの「Code → Download ZIP」機能を使うと、バイナリファイルが正しく含まれない場合があります。

#### 方法1: Git Clone（推奨）

```powershell
# リポジトリをクローン
git clone https://github.com/kimshow/autozipunzip.git
cd autozipunzip

# ファイルが存在するか確認
dir signed\20260105_test.zip

# MD5確認（macOS側の値: 576d6df99faf2d36fc0dbcfd252cc439）
CertUtil -hashfile signed\20260105_test.zip MD5

# 解凍テスト
Expand-Archive -Path "signed\20260105_test.zip" -DestinationPath "test_extract" -Force
dir test_extract -Recurse
```

#### 方法2: 直接ダウンロード（Git不要）

```powershell
# PowerShellで直接ダウンロード
Invoke-WebRequest -Uri "https://github.com/kimshow/autozipunzip/raw/main/signed/20260105_test.zip" -OutFile "test.zip"

# MD5確認
CertUtil -hashfile test.zip MD5

# 解凍
Expand-Archive -Path "test.zip" -DestinationPath "test_extract" -Force
dir test_extract -Recurse
```

ブラウザで直接開く場合：
```
https://github.com/kimshow/autozipunzip/raw/main/signed/20260105_test.zip
```

### macOSでの事前確認

```bash
# ZIPの内容を確認
unzip -l signed/YYYYMMDD_text.zip

# 日本語ファイル名が含まれているか確認
unzip -l signed/YYYYMMDD_text.zip | grep -E '[\x80-\xFF]'

# ZIP整合性検証
python3 tests/verify_zip_integrity.py signed/20260105_test.zip

# UTF-8フラグ詳細診断
python3 tests/diagnose_zip.py signed/20260105_test.zip
```

## 🛠️ トラブルシューティング

### Windows: 「指定されたファイルが見つかりません」

**原因**: GitHubの「Download ZIP」機能を使用した場合、テストZIPファイルが含まれていない可能性があります。

**解決策**: 
- `git clone`を使用する（上記「方法1」参照）
- または直接ダウンロードURLを使用する（上記「方法2」参照）

### Windows: 「フォルダーは空です」/ 7-Zip: 「有効なアーカイブではありません」

**原因**: `.gitattributes`設定前に取得したリポジトリで、ZIPファイルの改行コードが変換されている可能性があります。

**解決策**:
```powershell
# リポジトリを削除して再クローン
Remove-Item -Recurse -Force autozipunzip
git clone https://github.com/kimshow/autozipunzip.git
```

### エラー: "Python 3.11+ required"

- Python 3.11以上をインストールしてください
- GitHub Actionsでは自動的に3.11が使用されます

### エラー: "Cannot find 'connect/バイナリ'"

- ZIPファイルの構造を確認してください
- スクリプトは自動的に代替パスを検索します

### Windows で文字化けする

- `metadata_encoding='utf-8'` が使用されているか確認
- Python 3.11以上で実行されているか確認
- ZIP内のファイル名がUTF-8フラグ（0x800）付きで保存されているか診断ツールで確認

## 📋 必要要件

- **Python**: 3.11以上（UTF-8デフォルト対応必須）
- **GitHub Actions**: macOS-latest ランナー
- **依存関係**: 標準ライブラリのみ（外部パッケージ不要）

## 📖 詳細ドキュメント

- [実装計画](IMPLEMENTATION_PLAN.md) - 設計と技術詳細
- [レビュー結果](REVIEW_RESULT.md) - Win/Mac環境差異対策
- [Copilot指示](.github/copilot-instructions.md) - AI agent向けガイド

## 🔐 セキュリティ

- **パストラバーサル対策**: 解凍時にパスを検証
- **Zip爆弾**: 信頼できる内部ワークフロー向けのため対策なし
- **パーミッション**: ファイル権限を保持して再圧縮

## 📝 ライセンス

このプロジェクトは内部使用を想定しています。
