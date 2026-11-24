param([switch]$SkipInventory, [switch]$SkipBuild)
$ErrorActionPreference = 'Continue'
$root = 'C:\Users\imran\Documents\thesis research\Hybrid Voting and Percentage-Sweep Feature Selection for Ransomware Detection from Sysmon Events'
Set-Location $root

if (-not $SkipBuild) {
    python thesis\scripts\build.py
    if ($LASTEXITCODE -ne 0) { Write-Host 'BUILD FAILED'; exit 1 }
}

# clean any running soffice instances
Stop-Process -Name soffice,soffice.bin -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

$docx = Join-Path $root 'thesis\build\thesis.docx'
$pdf = Join-Path $root 'thesis\build\thesis.pdf'
Remove-Item -Force $pdf -ErrorAction SilentlyContinue

$argStr = '--headless --convert-to pdf --outdir "' + $root + '\thesis\build" "' + $docx + '"'
$p = Start-Process -FilePath 'C:\Program Files\LibreOffice\program\soffice.exe' -ArgumentList $argStr -Wait -PassThru -NoNewWindow
Write-Host "soffice exit: $($p.ExitCode)"

if (-not (Test-Path $pdf)) { Write-Host 'NO PDF PRODUCED'; exit 1 }
Write-Host ("pdf mtime: " + (Get-Item $pdf).LastWriteTime)

$env:PYTHONIOENCODING = 'utf-8'
if (-not $SkipInventory) {
    python thesis\scripts\page_inventory.py $pdf 2>&1 | Out-String -Width 220 | Write-Host
} else {
    python -c "import pymupdf; d = pymupdf.open(r'$pdf'); print('PDF pages:', d.page_count)"
}
