# A8 controller-off confirmation, i7Win11B share: seeds 2406-2407 (20 streams), 7 workers. Resumable: just start again.
$ErrorActionPreference = "Continue"
Set-Location (Split-Path -Parent $PSScriptRoot)
New-Item -ItemType Directory results_ctrloff_i7 -Force | Out-Null
"$(Get-Date -Format s) run_ctrloff_i7.ps1 start" | Add-Content results_ctrloff_i7\run_log.txt
python -u src\run_ctrloff.py run --out results_ctrloff_i7 --machine i7Win11B --seeds 2406-2407 --nw 7
"$(Get-Date -Format s) run_ctrloff_i7.ps1 finished" | Add-Content results_ctrloff_i7\run_log.txt