<#
.SYNOPSIS
    Copies the selected color books (*.acb) into the ColorBooks folder of every
    installed Revit version (C:\ProgramData\Autodesk\RVT <year>\ColorBooks).

    Run without -Books / -All to pick the color books from a numbered list.

.EXAMPLE
    .\install.ps1                          # choose color books from a list, all Revit versions
    .\install.ps1 -All                     # every color book, no questions
    .\install.ps1 -Books W7k.*             # only the W7k color books
    .\install.ps1 -Books RAL*,Named*       # pick by file name (wildcards allowed)
    .\install.ps1 -Year 2024               # only Revit 2024
    .\install.ps1 -Uninstall               # choose color books to remove
    .\install.ps1 -Uninstall -All          # remove every color book from this repository
#>
param(
    [string]$Year,
    [string[]]$Books,
    [switch]$All,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$source = Join-Path $PSScriptRoot "ColorBooks"

# W7k books first, then the contributed ones
$available = @(Get-ChildItem -Path $source -Filter "*.acb" -File) +
             @(Get-ChildItem -Path (Join-Path $source "Contributed") -Filter "*.acb" -File -ErrorAction SilentlyContinue)

function Get-BookLabel($file) {
    try { $name = ([xml](Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8)).colorBook.bookName } catch { $name = $null }
    if ($file.Directory.Name -eq "Contributed") { $group = "contributed" } else { $group = "W7k" }
    if (-not $name) { $name = $file.BaseName }
    "{0,-45} [{1}]" -f $name, $group
}

function Read-Selection {
    $verb = if ($Uninstall) { "remove" } else { "install" }
    Write-Host ""
    Write-Host "Available color books:"
    for ($i = 0; $i -lt $available.Count; $i++) {
        Write-Host ("  {0,2}. {1}" -f ($i + 1), (Get-BookLabel $available[$i]))
    }
    Write-Host ""
    Write-Host "Which color books do you want to $verb`?"
    Write-Host "  Numbers and ranges, e.g. 1,3,5-7  |  all  |  Enter = the 3 W7k books  |  q = quit"
    while ($true) {
        $answer = (Read-Host "Selection").Trim()
        if ($answer -eq "q") { exit 0 }
        if ($answer -eq "") { return @($available | Where-Object { $_.Name -like "W7k.*" }) }
        if ($answer -eq "all") { return $available }
        $picked = @()
        $ok = $true
        foreach ($part in ($answer -split "[,\s]+" | Where-Object { $_ })) {
            if ($part -match "^(\d+)-(\d+)$") { $range = [int]$Matches[1]..[int]$Matches[2] }
            elseif ($part -match "^\d+$") { $range = @([int]$part) }
            else { $ok = $false; break }
            foreach ($n in $range) {
                if ($n -lt 1 -or $n -gt $available.Count) { $ok = $false; break }
                $picked += $available[$n - 1]
            }
        }
        if ($ok -and $picked) { return @($picked | Sort-Object FullName -Unique) }
        Write-Host "Could not read '$answer'. Use numbers from 1 to $($available.Count), e.g. 1,3,5-7."
    }
}

if ($All) {
    $selected = $available
} elseif ($Books) {
    $selected = @($available | Where-Object { $f = $_; $Books | Where-Object { $f.BaseName -like $_ -or $f.Name -like $_ } })
    if (-not $selected) {
        Write-Warning "No color book matches: $($Books -join ', ')"
        exit 1
    }
} else {
    $selected = Read-Selection
}

$pattern = if ($Year) { "RVT $Year" } else { "RVT *" }
$targets = Get-ChildItem -Path "$env:ProgramData\Autodesk" -Directory -Filter $pattern -ErrorAction SilentlyContinue

if (-not $targets) {
    Write-Warning "No Revit folder matching '$pattern' found in $env:ProgramData\Autodesk."
    exit 1
}

Write-Host ""
Write-Host "Selected: $(($selected | ForEach-Object { $_.BaseName }) -join ', ')"

foreach ($rvt in $targets) {
    $dest = Join-Path $rvt.FullName "ColorBooks"
    try {
        if ($Uninstall) {
            $removed = 0
            foreach ($book in $selected) {
                $target = Join-Path $dest $book.Name
                if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target; $removed++ }
            }
            Write-Host "Removed $removed color book(s) from $dest"
        } else {
            New-Item -ItemType Directory -Path $dest -Force | Out-Null
            $selected | Copy-Item -Destination $dest -Force
            Write-Host "Installed $($selected.Count) color book(s) -> $dest"
        }
    } catch {
        Write-Warning "Could not write to $dest. Re-run PowerShell as Administrator. ($($_.Exception.Message))"
    }
}

Write-Host "Done. Restart Revit if it was open."
