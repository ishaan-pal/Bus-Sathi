# Forwards Windows :8000 -> WSL backend (required for physical Android on WSL2).
# Run in PowerShell as Administrator:
#   .\scripts\forward-api-port.ps1

$ErrorActionPreference = "Stop"

$wslIp = (wsl hostname -I).Trim().Split(" ")[0]
if (-not $wslIp) {
    Write-Error "Could not detect WSL IP. Start WSL and the backend first."
}

netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>$null | Out-Null
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp

$ruleName = "Haryana Roadways API"
if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 | Out-Null
}

$lanIp = (
    Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object {
        $_.InterfaceAlias -notmatch "Loopback|vEthernet" -and
        $_.IPAddress -notmatch "^169\."
    } |
    Select-Object -First 1
).IPAddress

Write-Host ""
Write-Host "API port forward active:"
Write-Host "  Phone / LAN  -> http://${lanIp}:8000"
Write-Host "  WSL backend  -> $wslIp:8000"
Write-Host ""
Write-Host "Run the app with:"
Write-Host "  flutter run --dart-define=API_HOST=$lanIp"
Write-Host ""
