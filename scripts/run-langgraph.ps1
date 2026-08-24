$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

& "$PSScriptRoot\..\.venv\Scripts\python.exe" -m langgraph_cli dev --config "$PSScriptRoot\..\langgraph.json" --allow-blocking
