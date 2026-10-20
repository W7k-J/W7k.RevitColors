<#
.SYNOPSIS
    Copies the W7k color books (*.acb) into the ColorBooks folder of every
    installed Revit version (C:\ProgramData\Autodesk\RVT <year>\ColorBooks).

.EXAMPLE
    .\install.ps1              # all installed Revit versions
    .\install.ps1 -Year 2024   # only Revit 2024
    .\install.ps1 -Uninstall   # remove W7k color books again
#>
param(
    [string]$Year,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$source  = Join-Path $PSScriptRoot "ColorBooks"
$books   = Get-ChildItem -Path $source -Filter "W7k.*.acb"
$pattern = if ($Year) { "RVT $Year" } else { "RVT *" }
$targets = Get-ChildItem -Path "$env:ProgramData\Autodesk" -Directory -Filter $pattern -ErrorAction SilentlyContinue

if (-not $targets) {
    Write-Warning "No Revit folder matching '$pattern' found in $env:ProgramData\Autodesk."
    exit 1
}

foreach ($rvt in $targets) {
    $dest = Join-Path $rvt.FullName "ColorBooks"
    try {
        if ($Uninstall) {
            Get-ChildItem -Path $dest -Filter "W7k.*.acb" -ErrorAction SilentlyContinue | Remove-Item
            Write-Host "Removed W7k color books from $dest"
        } else {
            New-Item -ItemType Directory -Path $dest -Force | Out-Null
            $books | Copy-Item -Destination $dest -Force
            Write-Host "Installed $($books.Count) color book(s) -> $dest"
        }
    } catch {
        Write-Warning "Could not write to $dest. Re-run PowerShell as Administrator. ($($_.Exception.Message))"
    }
}

Write-Host "Done. Restart Revit if it was open."
