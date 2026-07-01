$Repo = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location -LiteralPath $Repo.Path

python tools\foxclaw_commands.py

Write-Host ""
Write-Host "Useful next commands:"
Write-Host "  python tools\foxclaw_commands.py --list-ids"
Write-Host "  python tools\foxclaw_commands.py --show interaction-potential"
Write-Host "  python tools\foxclaw_commands.py --run source-discovery"
Write-Host "  python tools\foxclaw_commands.py --all-tools"
Write-Host ""
