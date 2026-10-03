# Runs diagnostic D4 (F_nometa, DESIGN.md A7) on the Vivobook: std + hard x seeds 2300-2307 (16 units), NW=14. Finished units are skipped -> simply start again after an interruption.
$ErrorActionPreference = "Continue"
Set-Location (Split-Path -Parent $PSScriptRoot)
New-Item -ItemType Directory results_vivo_diag -Force | Out-Null
"$(Get-Date -Format s) run_diag_vivo.ps1 nw=14 (D4, seeds 2300-2307)" | Add-Content results_vivo_diag\run_log.txt
python src\diag_i9.py run --suites D4 --nw 14 --seed0 2300 --n-seeds 8 --out results_vivo_diag
"$(Get-Date -Format s) run_diag_vivo.ps1 finished" | Add-Content results_vivo_diag\run_log.txt