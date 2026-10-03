# A8 controller-off confirmation, i9Win10 second share: seeds 2406-2407 (20 streams; planned for the i7, which went offline), 16 workers, BELOW-NORMAL priority. Resumable: just start again.
$ErrorActionPreference = "Continue"
(Get-Process -Id $PID).PriorityClass = "BelowNormal"
Set-Location (Split-Path -Parent $PSScriptRoot)
New-Item -ItemType Directory results_ctrloff_i9b -Force | Out-Null
"$(Get-Date -Format s) run_ctrloff_i9b.ps1 start" | Add-Content results_ctrloff_i9b\run_log.txt
python -u src\run_ctrloff.py run --out results_ctrloff_i9b --machine i9Win10 --seeds 2406-2407 --nw 16
"$(Get-Date -Format s) run_ctrloff_i9b.ps1 finished" | Add-Content results_ctrloff_i9b\run_log.txt