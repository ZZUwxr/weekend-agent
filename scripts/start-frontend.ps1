param(
    [int]$Port = 5187
)

$repoRoot = Split-Path -Parent $PSScriptRoot

function Test-PortInUse {
    try {
        $conn = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $Port -State Listen -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

if (Test-PortInUse) {
    Write-Host "Port $Port already in use, assuming Vite is running."
    exit 0
}

Write-Host "Starting Vite dev server..."

$proc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", "cd /d `"$repoRoot`" && npm run dev:android" `
    -WindowStyle Hidden `
    -PassThru

Write-Host "Vite dev server started (PID $($proc.Id)). Waiting for ready..."

$deadline = (Get-Date).AddSeconds(30)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 1
    if (Test-PortInUse) {
        Write-Host "Vite dev server is ready at http://127.0.0.1:$Port"
        exit 0
    }
    if ($proc.HasExited) {
        Write-Host "Vite process exited unexpectedly."
        exit 1
    }
}

Write-Host "Timeout waiting for Vite to start."
exit 1
