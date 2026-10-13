param(
    [string]$Range = "",
    [switch]$Notes,
    [string]$Root = (Join-Path $PSScriptRoot "..\..\..\..\복습노트"),
    [string]$OutDir = (Join-Path $env:USERPROFILE "Downloads")
)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path $Root).Path

# 날짜 폴더(4자리 숫자)만, 범위로 거른다
$all = Get-ChildItem $Root -Directory | Where-Object Name -match '^\d{4}$' | Sort-Object Name
$sel = if (-not $Range) { $all }
elseif ($Range -match '^(\d{4})-(\d{4})$') { $a, $b = $Matches[1], $Matches[2]; $all | Where-Object { $_.Name -ge $a -and $_.Name -le $b } }
elseif ($Range -match '^\d{4}(,\d{4})*$') { $want = $Range -split ','; $all | Where-Object { $want -contains $_.Name } }
else { throw "범위 형식 오류: '$Range' (MMDD, MMDD-MMDD, MMDD,MMDD)" }

$stage = Join-Path ([IO.Path]::GetTempPath()) ("ec2zip_" + [guid]::NewGuid())
New-Item -ItemType Directory $stage | Out-Null
$included = @(); $skipped = @()
foreach ($d in $sel) {
    $files = @(Get-ChildItem $d.FullName -File -Filter "복습문제_*.pdf")
    if ($Notes) { $files += @(Get-ChildItem $d.FullName -File -Filter "정리노트_*.html") }
    if ($files.Count -eq 0) { $skipped += $d.Name; continue }
    $files | Copy-Item -Destination $stage
    $included += $d.Name
}

if ($included.Count -eq 0) {
    Remove-Item $stage -Recurse -Force
    Write-Output "넣을 파일 없음. 있는 날짜: $($all.Name -join ', ')"
    exit 1
}

$prefix = if ($Notes) { "복습자료" } else { "복습문제" }
$span = if ($included.Count -eq 1) { $included[0] } else { "$($included[0])-$($included[-1])" }
$zip = Join-Path $OutDir "${prefix}_$span.zip"
Compress-Archive -Path "$stage\*" -DestinationPath $zip -Force
Remove-Item $stage -Recurse -Force

$size = [math]::Round((Get-Item $zip).Length / 1MB, 1)
Write-Output "ZIP: $zip ($size MB)"
Write-Output "포함: $($included -join ', ')"
if ($skipped) { Write-Output "건너뜀(파일 없음): $($skipped -join ', ')" }
