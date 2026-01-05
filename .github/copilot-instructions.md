# Copilot Instructions for autozipunzip

## Project Overview
GitHub Actions workflow for automated ZIP file decompression, code signing, and recompression with Windows compatibility.

**Use Case**: Process nested ZIP files containing Japanese filenames, apply code signing to XCFrameworks, and recompress maintaining UTF-8 encoding for Windows compatibility.

## Repository Structure
```
/
├── unsign/           # Input: unsigned ZIP files
├── signed/           # Output: signed and recompressed ZIP files
├── .github/
│   └── workflows/    # GitHub Actions workflow definitions
└── scripts/          # Python scripts for ZIP operations
```

## Critical Requirements
1. **Japanese Filename Support**: All ZIP operations must preserve UTF-8 encoding
2. **Windows Compatibility**: Recompressed ZIPs must open correctly on Windows (from macOS runner)
3.Local testing
python scripts/process_zip.py unsign/YYYYMMDD_text.zip signed/

# GitHub Actions triggers
# - Push to main with files in unsign/
# - Manual workflow_dispatch
```

## Project-Specific Conventions
- **ZIP Encoding**: Python 3.11+ uses UTF-8 by default for ZIP filenames (Windows compatible)
- **Path Handling**: Use `pathlib.Path` + always convert to POSIX (`as_posix()`) for ZIP arcnames
- **Logging**: Print step-by-step progress for GitHub Actions visibility
- **Cleanup**: Use `try-finally` to ensure temp directories are always removed
- **Error Handling**: Preserve original files on failure, log full stack traces

## Technical Stack
- **Python 3.11+**: **Required** for default UTF-8 encoding in ZIP files
- **GitHub Actions**: macOS-latest runner (manual trigger only for testing)
- **Python Scripts**: Add type hints and docstrings with Japanese filename examples
- **GitHub Actions**: Comment each step with Japanese context
- **Testing**: Create fixture ZIPs with Japanese filenames in `tests/`
- **Documentation**: Provide Windows verification steps in README

## Security Considerations
- **Path Traversal**: Validate extracted paths stay within target directory
- **Zip Bombs**: Not a concern for trusted internal workflows
- **Permissions**: Preserve file permissions during recompression

## Common Pitfalls to Avoid
1. **Encoding Issues**: Don't use `shutil.make_archive()` (no UTF-8 control)
2. **Path Separators**: Always use `/` in ZIP arcnames, not `\`
3. **Empty Directories**: `zipfile` doesn't preserve empty dirs by default
4. **Compression Level**: Use `ZIP_DEFLATED` (not `ZIP_STORED`) for size reduction
5. **Working Directory**: Change to parent dir before compression to avoid nested root folders

## References
- Python zipfile UTF-8: https://docs.python.org/3/library/zipfile.html
- GitHub Actions macOS runner: https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners

### Nested Directory Compression
```python
# Include all subdirectories and files
for root, dirs, files in os.walk(source_dir):
    for file in files:
        file_path = Path(root) / file
        # 重要: as_posix()でWindows互換の区切り文字に変換
        arcname = file_path.relative_to(source_dir).as_posix()
        zf.write(file_path, arcname=arcname)
```

### Long Path Handling
```python
import tempfile
import shutil

# macOS最大パス長: 1024文字
# /tmp直下で作業してパス長を最小化
with tempfile.TemporaryDirectory(dir='/tmp', prefix='zip_') as tmpdir:
    work_dir = Path(tmpdir)
    # 処理...
    # try-finally不要（コンテキストマネージャーで自動削除）
```

## Workflow Steps
1. Extract `YYYYMMDD_text.zip`
2. Extract `connect/バイナリ/コネクト_vXX.YY.ZZ.zip`
3. Extract `aaa.xcframework.zip` and `bbb.xcframework.zip`
4. Apply codesign to frameworks (add "署名済み.txt" marker)
5. Recompress frameworks → recreate parent ZIPs → recreate root ZIP
6. Delete intermediate directories after each compression

## Architecture Patterns
- **GitHub Actions**: Primary orchestration (macOS runner)
- **Python Scripts**: ZIP operations with proper encoding handling
- **Directory Management**: Clean up after each compression step

## Development Workflow
```bash
# Common commands to discover:
# - Installation: pip install -e ., npm install, go build
# - Tests: pytest, npm test, go test ./...
# - Linting: ruff, eslint, golangci-lint
```

## Project-Specific Conventions
- **Logging**: Use structured logging for file operations (which files processed, success/failure)
- **Path Handling**: Always use absolute paths or properly resolve relative paths
- **Safety**: Implement dry-run mode before actual file operations
- **Compression Options**: Support configurable compression levels

## External Dependencies
- Archive libraries: zipfile (Python), archiver/zip (Go), JSZip (Node.js)
- File system watchers: watchdog, chokidar, fsnotify
- CLI frameworks: click/typer, commander/yargs, cobra

## When Creating New Files
- Add clear docstrings/comments explaining ZIP operation logic
- Include examples in README showing common use cases
- Create tests with sample ZIP files in `tests/fixtures/` or similar
- Document CLI flags and their effects

## Security Considerations
- Validate ZIP file paths to prevent directory traversal attacks (zip bombs, path traversal)
- Set reasonable file size limits
- Handle symbolic links safely

## Key Questions to Ask User
- Target language/runtime? (Python, Node.js, Go, Rust)
- Supported platforms? (Windows, macOS, Linux, all)
- GUI needed or CLI-only?
- Integration requirements? (API, webhooks, scheduled tasks)
