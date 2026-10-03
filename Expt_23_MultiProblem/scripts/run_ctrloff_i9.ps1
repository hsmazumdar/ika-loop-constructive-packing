# A8 controller-off confirmation, i9Win10 share: seeds 2400-2405 (60 streams), 10 workers, BELOW-NORMAL priority (children inherit it). Resumable: just start again.
$ErrorActionPreference = "Continue"
(Get-Process -Id $PID).PriorityClass = "BelowNormal"
Set-Location (Split-Path -Parent $PSScriptRoot)
New-Item -ItemType Directory results_ctrloff_i9 -Force | Out-Null
"$(Get-Date -Format s) run_ctrloff_i9.ps1 start" | Add-Content results_ctrloff_i9\run_log.txt
python -u src\run_ctrloff.py run --out results_ctrloff_i9 --machine i9Win10 --seeds 2400-2405 --nw 10
"$(Get-Date -Format s) run_ctrloff_i9.ps1 finished" | Add-Content results_ctrloff_i9\run_log.txt