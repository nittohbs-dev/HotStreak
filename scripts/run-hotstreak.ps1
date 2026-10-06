param(
    [string]$Python = 'python',
    [int]$Port = 8010,
    [string]$JoinOrigin = '',
    [switch]$Windowed
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$previousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = "$projectRoot/src;$previousPythonPath"
$env:PYTHONDONTWRITEBYTECODE = '1'
if (-not $JoinOrigin) {
    $network = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.IPv4Address } | Select-Object -First 1
    $address = if ($network) { $network.IPv4Address.IPAddress | Select-Object -First 1 } else { '127.0.0.1' }
    $JoinOrigin = "http://${address}:$Port"
}
$server = $null
Push-Location $projectRoot
try {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($listener) { throw "Port $Port is already in use. Choose another -Port or stop the previous server." }
    $outLog = Join-Path $env:TEMP "hotstreak-$PID.stdout.log"
    $errLog = Join-Path $env:TEMP "hotstreak-$PID.stderr.log"
    $server = Start-Process -FilePath $Python -ArgumentList @('-m', 'uvicorn', 'hotstreak_sync.app:app', '--host', '0.0.0.0', '--port', "$Port") -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput $outLog -RedirectStandardError $errLog -PassThru
    $ready = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        if ($server.HasExited) { throw "Server exited. See $errLog" }
        try {
            $null = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/openapi.json" -TimeoutSec 1
            $ready = $true
            break
        } catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $ready) { throw "Server did not start. See $errLog" }
    $displayArgs = @('-m', 'hotstreak_display.live', '--server', "http://127.0.0.1:$Port", '--join-origin', $JoinOrigin)
    if ($Windowed) { $displayArgs += '--windowed' }
    & $Python @displayArgs
    if ($LASTEXITCODE -ne 0) { throw "Display exited with code $LASTEXITCODE" }
} finally {
    if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id }
    $env:PYTHONPATH = $previousPythonPath
    Pop-Location
}
