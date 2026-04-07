# Copy local F&M preloaded CSVs to DBFS for notebooks / Genie staging.
# Prereq: Databricks CLI v0.205+ logged in (`databricks auth login` or `databricks configure`).
#
# Usage (from anywhere):
#   .\scripts\databricks\copy_preload_to_dbfs.ps1
# Optional destination:
#   $env:DBFS_DEST = "dbfs:/FileStore/my_team/fmb_bank"; .\scripts\databricks\copy_preload_to_dbfs.ps1

$ErrorActionPreference = "Stop"

$RepoRoot = (Get-Item $PSScriptRoot).Parent.Parent.FullName
$Src = Join-Path $RepoRoot "data\preloaded\fmb_bank"
$Dest = if ($env:DBFS_DEST) { $env:DBFS_DEST } else { "dbfs:/FileStore/fmb_bank" }

if (-not (Test-Path $Src)) {
    Write-Error "Source folder not found: $Src"
}

Write-Host "Copying:" -ForegroundColor Cyan
Write-Host "  From: $Src"
Write-Host "  To:   $Dest"
Write-Host ""

databricks fs cp -r $Src $Dest

Write-Host ""
Write-Host "Done. In a notebook use path like: $Dest/customers.csv" -ForegroundColor Green
Write-Host "Or run load_fmb_bank_to_uc with: BASE_PATH = '$Dest'" -ForegroundColor Green
