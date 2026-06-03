param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8000,
    [string]$LlmProvider = "openai",
    [string]$AgentRuntime = "react",
    [string]$AllowRuleBasedFallback = "false"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$runtimeDir = Join-Path $repoRoot ".backend-runtime"
$stdoutLog = Join-Path $runtimeDir "backend.log"
$stderrLog = Join-Path $runtimeDir "backend.err.log"
$pidFile = Join-Path $runtimeDir "backend.pid"
$envFile = Join-Path $runtimeDir "backend.env"
$sourceStampFile = Join-Path $runtimeDir "backend.source"
$rootEnvFile = Join-Path $repoRoot ".env"
$backendEnvFile = Join-Path $backendDir ".env"
$managedEnvKeys = @(
    "LLM_PROVIDER",
    "AGENT_RUNTIME",
    "LLM_ALLOW_RULE_BASED_FALLBACK",
    "LLM_API_KEY",
    "OPENAI_API_KEY",
    "LLM_BASE_URL",
    "LLM_MODEL",
    "LLM_API_STYLE",
    "LLM_TIMEOUT_SECONDS",
    "LLM_MAX_RETRIES",
    "LLM_TEMPERATURE",
    "LLM_TRUST_ENV",
    "DATA_DIR"
)

function Read-DotEnvValues {
    $values = @{}
    foreach ($file in @($rootEnvFile, $backendEnvFile)) {
        if (-not (Test-Path -LiteralPath $file)) {
            continue
        }
        foreach ($line in (Get-Content -LiteralPath $file)) {
            if ($line -notmatch '^\s*([^#][^=]+?)\s*=\s*(.*)\s*$') {
                continue
            }
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            if (
                ($value.StartsWith('"') -and $value.EndsWith('"')) -or
                ($value.StartsWith("'") -and $value.EndsWith("'"))
            ) {
                $value = $value.Substring(1, $value.Length - 2)
            }
            $values[$key] = $value
        }
    }
    return $values
}

$dotEnvValues = Read-DotEnvValues

function Get-ConfiguredEnvValue {
    param(
        [string]$Name,
        [string]$Default = ""
    )
    if ($dotEnvValues.ContainsKey($Name)) {
        return [string]$dotEnvValues[$Name]
    }
    $current = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ($current) {
        return $current
    }
    return $Default
}

function Get-EnvFileStamp {
    $parts = New-Object System.Collections.Generic.List[string]
    foreach ($file in @($rootEnvFile, $backendEnvFile)) {
        if (Test-Path -LiteralPath $file) {
            $item = Get-Item -LiteralPath $file
            $parts.Add("$($item.Name):$($item.Length):$($item.LastWriteTimeUtc.Ticks)")
        } else {
            $parts.Add("missing:$([IO.Path]::GetFileName($file))")
        }
    }
    return ($parts -join ";")
}

function Test-BackendReady {
    try {
        $health = Invoke-RestMethod -Uri "http://${HostName}:$Port/api/v1/health" -TimeoutSec 2
        return $health.status -eq "ok"
    } catch {
        return $false
    }
}

function Get-DesiredEnvText {
    return @(
        "LLM_PROVIDER=$LlmProvider",
        "AGENT_RUNTIME=$AgentRuntime",
        "LLM_ALLOW_RULE_BASED_FALLBACK=$AllowRuleBasedFallback",
        "LLM_BASE_URL=$(Get-ConfiguredEnvValue -Name 'LLM_BASE_URL')",
        "LLM_MODEL=$(Get-ConfiguredEnvValue -Name 'LLM_MODEL')",
        "LLM_API_STYLE=$(Get-ConfiguredEnvValue -Name 'LLM_API_STYLE')",
        "DATA_DIR=$(Get-ConfiguredEnvValue -Name 'DATA_DIR')",
        "LLM_API_KEY_PRESENT=$([bool](Get-ConfiguredEnvValue -Name 'LLM_API_KEY'))",
        "OPENAI_API_KEY_PRESENT=$([bool](Get-ConfiguredEnvValue -Name 'OPENAI_API_KEY'))",
        "ENV_FILE_STAMP=$(Get-EnvFileStamp)"
    ) -join "`n"
}

function Test-BackendEnvMatches {
    if (-not (Test-Path -LiteralPath $envFile)) {
        return $false
    }
    return ((Get-Content -LiteralPath $envFile -Raw).Trim() -eq (Get-DesiredEnvText).Trim())
}

function Get-BackendSourceStamp {
    if (-not (Test-Path -LiteralPath $backendDir)) {
        return ""
    }
    $sourceFiles = Get-ChildItem -LiteralPath $backendDir -Recurse -File -Include *.py, pyproject.toml
    if (-not $sourceFiles) {
        return "0:0"
    }
    $latestWrite = ($sourceFiles | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum
    return "$($sourceFiles.Count):$($latestWrite.Ticks)"
}

function Test-BackendSourceMatches {
    if (-not (Test-Path -LiteralPath $sourceStampFile)) {
        return $false
    }
    return ((Get-Content -LiteralPath $sourceStampFile -Raw).Trim() -eq (Get-BackendSourceStamp).Trim())
}

function Stop-ManagedBackend {
    if (-not (Test-Path -LiteralPath $pidFile)) {
        return $false
    }
    $existingPid = [int](Get-Content -LiteralPath $pidFile -Raw)
    $process = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
    if (-not $process) {
        return $false
    }
    $listener = Get-NetTCPConnection -LocalAddress $HostName -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener -and $listener.OwningProcess -ne $existingPid) {
        return $false
    }
    Write-Host "Restarting Weekend Agent backend to apply local Android runtime settings."
    Stop-Process -Id $existingPid -Force
    $deadline = (Get-Date).AddSeconds(10)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 250
        $listener = Get-NetTCPConnection -LocalAddress $HostName -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if (-not $listener) {
            return $true
        }
    }
    return $true
}

function Get-PythonCandidates {
    $candidates = New-Object System.Collections.Generic.List[string]
    if ($env:WEEKEND_AGENT_PYTHON) {
        $candidates.Add($env:WEEKEND_AGENT_PYTHON)
    }

    foreach ($cmd in (Get-Command python -All -ErrorAction SilentlyContinue)) {
        if ($cmd.Source) {
            $candidates.Add($cmd.Source)
        }
    }

    $commonPaths = @(
        "D:\Anaconda3\envs\multimodal_assistant\python.exe",
        "D:\Anaconda3\python.exe",
        "D:\Program Files\Python\Python311\python.exe"
    )
    foreach ($path in $commonPaths) {
        if (Test-Path -LiteralPath $path) {
            $candidates.Add($path)
        }
    }

    return $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
}

function Get-BackendPythonPath {
    $paths = New-Object System.Collections.Generic.List[string]
    if ($env:PYTHONPATH) {
        foreach ($item in ($env:PYTHONPATH -split [IO.Path]::PathSeparator)) {
            if ($item) { $paths.Add($item) }
        }
    }

    $knownSitePackages = @(
        "C:\Users\wxr\AppData\Roaming\Python\Python311\site-packages",
        "D:\Anaconda3\envs\multimodal_assistant\Lib\site-packages"
    )
    foreach ($path in $knownSitePackages) {
        if (Test-Path -LiteralPath $path) {
            $paths.Add($path)
        }
    }
    $paths.Add($backendDir)

    return (($paths | Select-Object -Unique) -join [IO.Path]::PathSeparator)
}

function Test-PythonBackendDeps {
    param(
        [string]$PythonExe,
        [string]$PythonPath = ""
    )
    $previousPythonPath = $env:PYTHONPATH
    try {
        if ($PythonPath) {
            $env:PYTHONPATH = $PythonPath
        }
        & $PythonExe -c "import fastapi, uvicorn, pydantic, pydantic_settings" *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    } finally {
        $env:PYTHONPATH = $previousPythonPath
    }
}

function Resolve-BackendPython {
    $backendPythonPath = Get-BackendPythonPath
    foreach ($candidate in (Get-PythonCandidates)) {
        if (Test-PythonBackendDeps -PythonExe $candidate) {
            return @{ Python = $candidate; PythonPath = "" }
        }
        if (Test-PythonBackendDeps -PythonExe $candidate -PythonPath $backendPythonPath) {
            return @{ Python = $candidate; PythonPath = $backendPythonPath }
        }
    }
    Write-Error "No Python runtime with backend dependencies was found. Install backend dependencies with 'pip install -e backend' or set WEEKEND_AGENT_PYTHON to a compatible python.exe."
    exit 1
}

if (Test-BackendReady) {
    if ((Test-BackendEnvMatches) -and (Test-BackendSourceMatches)) {
        Write-Host "Weekend Agent backend already running at http://${HostName}:$Port"
        exit 0
    }
    if (-not (Stop-ManagedBackend)) {
        Write-Error "Weekend Agent backend is already running at http://${HostName}:$Port, but it was not started with the current Android local runtime settings or backend source."
        exit 1
    }
}

$listener = Get-NetTCPConnection -LocalAddress $HostName -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    Write-Error "Port $Port is already in use, but /api/v1/health did not respond as Weekend Agent."
    exit 1
}

if (-not (Test-Path -LiteralPath $backendDir)) {
    Write-Error "Backend directory not found: $backendDir"
    exit 1
}

$pythonRuntime = Resolve-BackendPython

New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null

$args = @(
    "-m",
    "uvicorn",
    "local_explorer_agent.app.main:app",
    "--host",
    $HostName,
    "--port",
    "$Port"
)

$previousManagedEnv = @{}
foreach ($key in $managedEnvKeys) {
    $previousManagedEnv[$key] = [Environment]::GetEnvironmentVariable($key, "Process")
}
$previousPythonPath = $env:PYTHONPATH
try {
    foreach ($key in $managedEnvKeys) {
        if ($dotEnvValues.ContainsKey($key)) {
            [Environment]::SetEnvironmentVariable($key, [string]$dotEnvValues[$key], "Process")
        }
    }
    $env:LLM_PROVIDER = $LlmProvider
    $env:AGENT_RUNTIME = $AgentRuntime
    $env:LLM_ALLOW_RULE_BASED_FALLBACK = $AllowRuleBasedFallback
    if ($pythonRuntime.PythonPath) {
        $env:PYTHONPATH = $pythonRuntime.PythonPath
    }

    $process = Start-Process `
        -FilePath $pythonRuntime.Python `
        -ArgumentList $args `
        -WorkingDirectory $backendDir `
        -RedirectStandardOutput $stdoutLog `
        -RedirectStandardError $stderrLog `
        -WindowStyle Hidden `
        -PassThru
} finally {
    foreach ($key in $managedEnvKeys) {
        [Environment]::SetEnvironmentVariable($key, $previousManagedEnv[$key], "Process")
    }
    $env:PYTHONPATH = $previousPythonPath
}

Set-Content -LiteralPath $pidFile -Value $process.Id
Set-Content -LiteralPath $envFile -Value (Get-DesiredEnvText)
Set-Content -LiteralPath $sourceStampFile -Value (Get-BackendSourceStamp)
Write-Host "Starting Weekend Agent backend (PID $($process.Id)) at http://${HostName}:$Port"

$deadline = (Get-Date).AddSeconds(35)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500
    if (Test-BackendReady) {
        Write-Host "Weekend Agent backend is ready."
        exit 0
    }
    if ($process.HasExited) {
        Write-Error "Backend process exited early. See $stderrLog"
        if (Test-Path -LiteralPath $stderrLog) {
            Get-Content -LiteralPath $stderrLog -Tail 40 | Write-Error
        }
        exit 1
    }
}

Write-Error "Timed out waiting for backend to become ready. See $stderrLog"
if (Test-Path -LiteralPath $stderrLog) {
    Get-Content -LiteralPath $stderrLog -Tail 40 | Write-Error
}
exit 1
