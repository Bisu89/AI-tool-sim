$ErrorActionPreference = "Stop"
if (Test-Path .\.venv\Scripts\python.exe) {
    .\.venv\Scripts\python.exe -m sim_designer.main
} else {
    py -3.11 -m sim_designer.main
}
