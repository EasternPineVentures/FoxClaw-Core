$WindowScript = Resolve-Path (Join-Path $PSScriptRoot "foxclaw_command_center_window.ps1")

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $WindowScript.Path
)
