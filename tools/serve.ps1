# 作成：2026-11-22
# 目的：練習アプリ（app/）を PC の localhost で起動する。Node.js が必要
# 使い方：./tools/serve.ps1            → http://localhost:8000/
#         ./tools/serve.ps1 -Port 8001 → 別のポートで起動
param([int]$Port = 8000)

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error 'Node.js が見つかりません。https://nodejs.org/ から入れてください'
    exit 1
}
node (Join-Path $PSScriptRoot 'serve.mjs') $Port
exit $LASTEXITCODE
