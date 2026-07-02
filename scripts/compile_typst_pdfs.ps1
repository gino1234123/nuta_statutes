param(
    [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$Recursive,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command typst -ErrorAction SilentlyContinue)) {
    throw "typst command not found. Please install Typst and make sure typst.exe is in PATH."
}

$rootPath = (Resolve-Path $Root).Path

$outputDir = Join-Path $rootPath "complied_pdf"
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$folders = Get-ChildItem -LiteralPath $rootPath -Directory |
    Where-Object { $_.Name -ne 'scripts' -and $_.Name -ne 'complied_pdf' } |
    Sort-Object Name

if (-not $folders) {
    Write-Warning "No folders (excluding 'scripts') were found under: $rootPath"
    exit 0
}

$typFiles = foreach ($folder in $folders) {
    Get-ChildItem -LiteralPath $folder.FullName -Filter "*.typ" -File -Recurse:($Recursive.IsPresent)
}

if (-not $typFiles) {
    Write-Warning "No .typ files were found in matching folders."
    exit 0
}

$failed = @()

foreach ($typ in $typFiles) {
    $pdf = Join-Path $outputDir "$([System.IO.Path]::GetFileNameWithoutExtension($typ.FullName)).pdf"

    if ($Clean -and (Test-Path -LiteralPath $pdf)) {
        Remove-Item -LiteralPath $pdf
    }

    Write-Host "Compiling $($typ.FullName) -> $pdf"

    & typst compile --root $rootPath $typ.FullName $pdf

    if ($LASTEXITCODE -ne 0) {
        $failed += $typ.FullName
        Write-Error "Compile failed: $($typ.FullName)" -ErrorAction Continue
    }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Write-Host "The following files failed to compile:"
    $failed | ForEach-Object { Write-Host "  $_" }
    exit 1
}

Write-Host ""
Write-Host "Done: compiled $($typFiles.Count) Typst file(s)."
