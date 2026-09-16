# Dot-source this script. This configures only the current process, never Live.
[CmdletBinding()]
param([string]$WorkspaceRoot = '', [string]$PythonPath = '')
$ErrorActionPreference = 'Stop'
$repoPath = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
if (-not $WorkspaceRoot) { $WorkspaceRoot = Split-Path -Parent $repoPath }
$WorkspaceRoot = [IO.Path]::GetFullPath($WorkspaceRoot)
if (-not $PythonPath) { $PythonPath = Join-Path $WorkspaceRoot 'env\v23\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath (Join-Path $repoPath '.git'))) { throw 'Git checkout이 아닙니다.' }
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw '개발 Python이 없습니다. workspace-portability.md를 확인하세요.' }
$version = & $PythonPath -B -c 'import sys; print(".".join(map(str,sys.version_info[:3])))'
if ($LASTEXITCODE -ne 0 -or $version -ne '3.12.10') { throw 'Python 3.12.10 개발 계약과 다릅니다.' }
$runtimeScripts = Split-Path -Parent $PythonPath
$tempPath = Join-Path $WorkspaceRoot 'tmp'
if (-not (Test-Path -LiteralPath $tempPath -PathType Container)) { throw 'workspace/tmp 폴더를 먼저 만드세요.' }
$env:VIRTUAL_ENV = Split-Path -Parent $runtimeScripts
$env:LAO_WORKSPACE_ROOT = $WorkspaceRoot
$env:PYTHONPATH = (Join-Path $repoPath 'stages\b1-sequential\src') + ';' + (Join-Path $repoPath 'tools\benchmark-runner\src')
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TEMP = $tempPath
$env:TMP = $env:TEMP
$remainingPath = @($env:PATH -split ';' | Where-Object { $_ -and $_.TrimEnd('\') -ine $runtimeScripts })
$env:PATH = $runtimeScripts + ';' + ($remainingPath -join ';')
Set-Location -LiteralPath $repoPath
Write-Output "개발 위치: $repoPath / Python: $PythonPath"
Write-Output '개발 환경 진입만 수행했습니다. Live는 별도 검증·승인이 필요합니다.'
