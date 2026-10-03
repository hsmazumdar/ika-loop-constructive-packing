# Runs the post-hoc diagnostics (DESIGN.md A7) in two stages; finished units are skipped, so this can simply be started again after an interruption.
$ErrorActionPreference = "Continue"
Set-Location (Split-Path -Parent $PSScriptRoot)
$nw = [int]((Get-CimInstance Win32_Processor | Measure-Object NumberOfCores -Sum).Sum) - 2
if ($nw -lt 1) { $nw = 1 }
"$(Get-Date -Format s) run_diag_i9.ps1 nw=$nw" | Add-Content results_i9\run_log.txt
python src\diag_i9.py run --suites D1 D2 --nw $nw
python src\diag_i9.py run --suites D3 D4 D2L --nw $nw
"$(Get-Date -Format s) run_diag_i9.ps1 finished" | Add-Content results_i9\run_log.txt