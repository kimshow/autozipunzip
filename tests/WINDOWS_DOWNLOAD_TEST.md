# Windows環境でのダウンロードテスト手順

## 問題の切り分け

「Download ZIP（リポジトリ全体）」では解凍できるが、「raw URL直接ダウンロード」では解凍できない場合、以下の原因が考えられます：

## テスト1: PowerShellでのダウンロード

```powershell
# 正しいダウンロード方法
Invoke-WebRequest -Uri "https://github.com/kimshow/autozipunzip/raw/main/signed/20260105_test.zip" -OutFile "test_raw.zip"

# MD5確認（期待値: 576d6df99faf2d36fc0dbcfd252cc439）
CertUtil -hashfile test_raw.zip MD5

# ファイルサイズ確認（期待値: 1341 bytes）
(Get-Item test_raw.zip).Length
```

## テスト2: ブラウザダウンロードの確認

ブラウザ（Chrome, Edge, Firefox）で以下のURLを開いた場合：
```
https://github.com/kimshow/autozipunzip/raw/main/signed/20260105_test.zip
```

### 確認ポイント

1. **ファイル名**: 
   - 正: `20260105_test.zip`
   - 誤: `20260105_test.zip.txt` や `20260105_test.zip.html`

2. **ファイルサイズ**: 
   - 正: 1,341 bytes (1.31 KB)
   - 誤: それ以外のサイズ

3. **ファイルの先頭バイト**:
```powershell
# バイナリエディタで開くか、以下を実行
Format-Hex test_raw.zip -Count 16
```

期待される出力（先頭16バイト）:
```
00000000   50 4B 03 04 14 00 00 08  08 00 0D 17 25 5C CD A7
           P  K  .  .  .  .  .  .   .  .  .  .  %  \  .  .
```

## 考えられる原因と対策

### 原因1: ブラウザがファイルをテキストとして扱っている

**症状**: ファイルサイズが異なる、または`.txt`が追加される

**対策**: PowerShellの`Invoke-WebRequest`を使用（上記テスト1）

### 原因2: ブラウザの「名前を付けて保存」時の文字コード変換

**症状**: ファイルサイズは同じだが中身が破損

**対策**: 
1. ブラウザの設定で「ダウンロード時の動作」を確認
2. 右クリック→「名前を付けてリンク先を保存」を使用
3. または`git clone`を使用

### 原因3: Windows Defenderによる検疫

**症状**: ダウンロード後すぐにファイルが消える、またはアクセスできない

**対策**: 
```powershell
# Windows Defenderの除外設定を確認
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
```

## 推奨: リポジトリ全体のダウンロードを使用

「Download ZIP」が成功するなら、それを推奨します：

1. https://github.com/kimshow/autozipunzip にアクセス
2. 「Code」→「Download ZIP」をクリック
3. ダウンロードしたZIPを解凍
4. `signed/20260105_test.zip`を使用

## または: Git for Windowsを使用

最も確実な方法：

```powershell
# Git for Windowsをインストール（まだの場合）
# https://git-scm.com/download/win

# リポジトリをクローン
git clone https://github.com/kimshow/autozipunzip.git
cd autozipunzip

# ファイル確認
dir signed\20260105_test.zip
CertUtil -hashfile signed\20260105_test.zip MD5
```

## デバッグ情報の収集

問題が解決しない場合、以下の情報を収集してください：

```powershell
# 1. ダウンロードしたファイルのMD5
CertUtil -hashfile test_raw.zip MD5

# 2. ファイルサイズ
(Get-Item test_raw.zip).Length

# 3. ファイルの先頭バイト
Format-Hex test_raw.zip -Count 32

# 4. ZIPとして認識されているか
Test-Path test_raw.zip -PathType Leaf

# 5. Windowsのバージョン
Get-ComputerInfo | Select-Object WindowsVersion, OsArchitecture

# 6. 使用したダウンロード方法
# - ブラウザ（Chrome/Edge/Firefox）
# - PowerShell Invoke-WebRequest
# - その他
```

## 期待される正常な結果

```
MD5: 576d6df99faf2d36fc0dbcfd252cc439
Size: 1341 bytes
Header: 50 4B 03 04 (PK..)
解凍: 成功（connect/バイナリ/コネクト_v1.0.0.zip が取り出せる）
```
