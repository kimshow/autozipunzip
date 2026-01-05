#!/usr/bin/env python3
"""
ZIPファイルの完全性検証ツール
Windows環境で「有効なアーカイブではありません」エラーの原因を特定
"""

import zipfile
import struct
import sys
from pathlib import Path


def verify_zip_structure(zip_path: Path) -> dict:
    """ZIPファイルの構造を詳細に検証"""
    results = {
        'valid': False,
        'errors': [],
        'warnings': [],
        'details': {}
    }
    
    try:
        # ファイルサイズチェック
        file_size = zip_path.stat().st_size
        results['details']['file_size'] = file_size
        
        if file_size < 22:  # 最小のZIPファイルサイズ（End of Central Directory）
            results['errors'].append(f"ファイルサイズが小さすぎます: {file_size} bytes")
            return results
        
        # バイナリで読み込んで構造チェック
        with open(zip_path, 'rb') as f:
            # Local File Header確認
            magic = f.read(4)
            if magic != b'PK\x03\x04':
                results['errors'].append(f"無効なZIPシグネチャ: {magic.hex()}")
                return results
            
            f.seek(0)
            content = f.read()
            
            # Central Directoryの位置を確認
            if b'PK\x01\x02' not in content:
                results['errors'].append("Central Directory File Headerが見つかりません")
            
            # End of Central Directoryの位置を確認
            if b'PK\x05\x06' not in content:
                results['errors'].append("End of Central Directory recordが見つかりません")
            else:
                # End of Central Directoryを解析
                eocd_offset = content.rfind(b'PK\x05\x06')
                f.seek(eocd_offset)
                eocd_data = f.read(22)
                
                if len(eocd_data) == 22:
                    # EOCD構造を解析
                    (signature, disk_num, disk_start, entries_disk, 
                     entries_total, cd_size, cd_offset, comment_len) = struct.unpack(
                        '<IHHHHIIH', eocd_data
                    )
                    
                    results['details']['eocd'] = {
                        'offset': eocd_offset,
                        'entries_total': entries_total,
                        'central_dir_size': cd_size,
                        'central_dir_offset': cd_offset,
                        'comment_length': comment_len
                    }
                    
                    # Central Directoryの位置が正しいか確認
                    if cd_offset + cd_size != eocd_offset:
                        results['warnings'].append(
                            f"Central Directoryの位置が不正: "
                            f"offset={cd_offset}, size={cd_size}, eocd={eocd_offset}"
                        )
        
        # zipfileモジュールで読み込みテスト
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # testzip()で整合性確認
            bad_file = zf.testzip()
            if bad_file:
                results['errors'].append(f"破損したファイル: {bad_file}")
            else:
                results['valid'] = True
            
            # 各エントリの検証
            results['details']['entries'] = []
            for info in zf.infolist():
                entry_info = {
                    'filename': info.filename,
                    'compress_type': info.compress_type,
                    'compress_size': info.compress_size,
                    'file_size': info.file_size,
                    'flag_bits': f'0x{info.flag_bits:04x}',
                    'crc': f'0x{info.CRC:08x}'
                }
                
                # 圧縮率チェック
                if info.file_size > 0:
                    ratio = info.compress_size / info.file_size
                    if ratio > 1.0:
                        results['warnings'].append(
                            f"{info.filename}: 圧縮後のサイズが大きい ({ratio:.2f})"
                        )
                
                # CRCの検証（実際に読み込んで確認）
                try:
                    data = zf.read(info.filename)
                    import zlib
                    calculated_crc = zlib.crc32(data) & 0xffffffff
                    if calculated_crc != info.CRC:
                        results['errors'].append(
                            f"{info.filename}: CRC不一致 "
                            f"(期待={info.CRC:08x}, 実際={calculated_crc:08x})"
                        )
                    entry_info['crc_verified'] = True
                except Exception as e:
                    results['errors'].append(f"{info.filename}: 読み込みエラー - {e}")
                    entry_info['crc_verified'] = False
                
                results['details']['entries'].append(entry_info)
    
    except zipfile.BadZipFile as e:
        results['errors'].append(f"BadZipFile: {e}")
    except Exception as e:
        results['errors'].append(f"予期しないエラー: {e}")
    
    return results


def print_results(zip_path: Path, results: dict):
    """検証結果を表示"""
    print("=" * 70)
    print(f"ZIP整合性検証: {zip_path.name}")
    print("=" * 70)
    
    # 基本情報
    print(f"\n📋 基本情報:")
    print(f"  ファイルパス: {zip_path}")
    print(f"  ファイルサイズ: {results['details'].get('file_size', 0):,} bytes")
    
    # EOCDの情報
    if 'eocd' in results['details']:
        eocd = results['details']['eocd']
        print(f"\n📦 End of Central Directory:")
        print(f"  エントリ数: {eocd['entries_total']}")
        print(f"  Central Directory offset: {eocd['central_dir_offset']}")
        print(f"  Central Directory size: {eocd['central_dir_size']}")
        print(f"  EOCD offset: {eocd['offset']}")
    
    # エントリ情報
    if results['details'].get('entries'):
        print(f"\n📄 エントリ詳細:")
        for entry in results['details']['entries']:
            crc_status = "✅" if entry.get('crc_verified') else "❌"
            print(f"  {crc_status} {entry['filename']}")
            print(f"     圧縮: {entry['compress_size']:,} bytes → {entry['file_size']:,} bytes")
            print(f"     CRC: {entry['crc']}, Flags: {entry['flag_bits']}")
    
    # 警告
    if results['warnings']:
        print(f"\n⚠️  警告 ({len(results['warnings'])}件):")
        for warning in results['warnings']:
            print(f"  - {warning}")
    
    # エラー
    if results['errors']:
        print(f"\n❌ エラー ({len(results['errors'])}件):")
        for error in results['errors']:
            print(f"  - {error}")
    
    # 結論
    print(f"\n{'='*70}")
    if results['valid'] and not results['errors']:
        print("✅ ZIPファイルは正常です")
    else:
        print("❌ ZIPファイルに問題があります")
    print("=" * 70)


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print(f"使用方法: {sys.argv[0]} <zipfile>")
        sys.exit(1)
    
    zip_path = Path(sys.argv[1])
    if not zip_path.exists():
        print(f"エラー: ファイルが見つかりません: {zip_path}")
        sys.exit(1)
    
    results = verify_zip_structure(zip_path)
    print_results(zip_path, results)
    
    sys.exit(0 if results['valid'] and not results['errors'] else 1)


if __name__ == "__main__":
    main()
