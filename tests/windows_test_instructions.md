# Windows環境でのZIPテスト手順

## 前提条件
- Windows 10/11
- テストファイル: `signed/20260105_test.zip`

## テスト1: Windows Explorer
```powershell
# 1. ZIPファイルをダブルクリック
# 2. 中身が表示されるか確認
# 3. 右クリック→「すべて展開」を実行

# エラーが出る場合、スクリーンショットとエラーメッセージを記録
```

## テスト2: PowerShell標準コマンド
```powershell
# PowerShellを開く
cd Desktop  # ZIPファイルを置いた場所

# 解凍テスト
Expand-Archive -Path "20260105_test.zip" -DestinationPath "test_extract" -Force

# 結果確認
dir test_extract -Recurse

# エラーが出る場合のログ収集
Expand-Archive -Path "20260105_test.zip" -DestinationPath "test_extract" -Force -Verbose 2>&1 | Out-File error_log.txt
```

## テスト3: 7-Zip（インストールされている場合）
```powershell
# コマンドライン
& "C:\Program Files\7-Zip\7z.exe" t "20260105_test.zip"  # 整合性テスト
& "C:\Program Files\7-Zip\7z.exe" l "20260105_test.zip"  # 内容表示
& "C:\Program Files\7-Zip\7z.exe" x "20260105_test.zip" -o"test_extract"  # 解凍

# GUIでも確認
# 右クリック→7-Zip→Open Archive
```

## テスト4: オンライン診断ツール
https://www.winziputil.com/analyze-zip.html
にZIPファイルをアップロードして診断結果を確認

## 記録が必要な情報
1. エラーメッセージの全文（日本語/英語どちらも）
2. どのツールで失敗したか
3. どの階層のZIPで失敗したか
4. 7-Zipの整合性テスト結果
5. Windows 10か11か
