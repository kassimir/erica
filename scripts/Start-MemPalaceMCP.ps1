# Start MemPalace MCP server against the Erica palace (~/.mempalace/erica_palace).
# Use from Cursor: claude mcp add mempalace -- pwsh -File path/to/Start-MemPalaceMCP.ps1
# Or run manually after: pip install mempalace

$ErrorActionPreference = "Stop"
$ericaRoot = Split-Path $PSScriptRoot -Parent
$venvActivate = Join-Path $ericaRoot "agent\.venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    . $venvActivate
}
$env:MEMPALACE_PALACE_PATH = "$env:USERPROFILE\.mempalace\erica_palace"
if (-not (Test-Path $env:MEMPALACE_PALACE_PATH)) {
    Write-Warning "Palace not found at $($env:MEMPALACE_PALACE_PATH). Run: mempalace init $env:MEMPALACE_PALACE_PATH"
}
python -m mempalace.mcp_server
