# 作成：2026-11-23
# 目的：回路図を生成し、KiCad 10 の形式にそろえ、確認（ERC・pins.h との突き合わせ）してから
#       回路図の画像（docs/schematic.svg）と部品表（hardware/bom.csv）を書き出す。どれか失敗したら止まる
# 使い方：./tools/build_schematic.ps1
#         KiCad の場所が違うときは -KiCad 'C:\Program Files\KiCad\10.0'
param([string]$KiCad = (Join-Path $env:LOCALAPPDATA 'Programs\KiCad\10.0'))

$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$cli = Join-Path $KiCad 'bin\kicad-cli.exe'
$sch = Join-Path $root 'hardware\cw-keyer.kicad_sch'
$tmp = Join-Path ([IO.Path]::GetTempPath()) 'cw-keyer-sch'
$env:PYTHONIOENCODING = 'utf-8'
New-Item -ItemType Directory -Force $tmp | Out-Null
if (-not (Test-Path $cli)) { throw "kicad-cli が見つかりません：$cli（-KiCad で KiCad のフォルダを指定してください）" }

# コマンドを実行し、失敗したら止める
function Invoke-Step([string]$name, [scriptblock]$cmd) {
    Write-Host "== $name"
    & $cmd
    if ($LASTEXITCODE -ne 0) { throw "$name に失敗しました（終了コード $LASTEXITCODE）" }
}

Invoke-Step '回路図を生成' { python (Join-Path $root 'tools\make_schematic.py') (Join-Path $KiCad 'share\kicad\symbols') }
Invoke-Step 'KiCad 10 の形式にそろえる' { & $cli sch upgrade $sch | Out-Null }

# ERC：違反が 1 件でもあれば止める（警告も含む）
$erc = Join-Path $tmp 'erc.json'
Invoke-Step 'ERC' { & $cli sch erc --format json --severity-all -o $erc $sch | Out-Null }
$violations = @((Get-Content $erc -Raw -Encoding utf8 | ConvertFrom-Json).sheets | ForEach-Object { $_.violations } | Where-Object { $_ })
if ($violations.Count -gt 0) {
    $violations | ForEach-Object { Write-Host "  $($_.severity): $($_.description)" }
    throw "ERC の違反が $($violations.Count) 件あります"
}
Write-Host '  違反 0 件'

$net = Join-Path $tmp 'cw-keyer.net'
Invoke-Step 'ネットリストを書き出す' { & $cli sch export netlist --format kicadsexpr -o $net $sch | Out-Null }
Invoke-Step 'pins.h と突き合わせる' { python (Join-Path $root 'tools\check_schematic.py') $net }

Invoke-Step '回路図の画像（SVG）' {
    & $cli sch export svg --exclude-drawing-sheet -o $tmp $sch | Out-Null
    # 書き出した日時が入るタイトルを固定する（作り直すたびに差分が出ないように）
    $svg = (Get-Content (Join-Path $tmp 'cw-keyer.svg') -Raw -Encoding utf8) -replace '<title>SVG Image created as [^<]*</title>', '<title>CW Keyer Trainer schematic</title>'
    [IO.File]::WriteAllText((Join-Path $root 'docs\schematic.svg'), $svg, [Text.UTF8Encoding]::new($false))
}
Invoke-Step '部品表（CSV）' {
    & $cli sch export bom -o (Join-Path $root 'hardware\bom.csv') `
        --fields 'Reference,Value,Note,${QUANTITY}' --labels '参照,値,メモ,数' `
        --group-by 'Value,Note' --sort-field 'Reference' $sch | Out-Null
}
Write-Host '完了：hardware/cw-keyer.kicad_sch・docs/schematic.svg・hardware/bom.csv'
