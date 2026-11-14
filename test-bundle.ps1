[CmdletBinding()]
param(
    [string]$OneFileExe = "dist\onefile\cage.exe",
    [string]$OneDirExe = "dist\onedir\cage\cage.exe"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Invoke-RancageChecked {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $Output = & $Executable @Arguments 2>&1
    $ExitCode = $LASTEXITCODE
    $Text = ($Output | Out-String).Trim()
    if ($ExitCode -ne 0) {
        throw "$Label failed (exit $ExitCode). Output: $Text"
    }
    return $Text
}

$Executables = @(
    (Resolve-Path -LiteralPath $OneFileExe).Path,
    (Resolve-Path -LiteralPath $OneDirExe).Path
)

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "cage-bundle-smoke-$PID"
New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null

try {
    foreach ($Executable in $Executables) {
        Write-Host "Smoke-testing $Executable" -ForegroundColor Cyan

        $Version = Invoke-RancageChecked -Executable $Executable -Arguments @("--version") -Label "Version check"
        if ($Version -notmatch "RANCAGE 0\.2\.0a1") {
            throw "Unexpected RANCAGE version: $Version"
        }

        [void](Invoke-RancageChecked -Executable $Executable -Arguments @("check", "examples\hello.cage") -Label "Source check")

        $RunOutput = Invoke-RancageChecked -Executable $Executable -Arguments @("run", "examples\hello.cage") -Label "Source run"
        if ($RunOutput -notmatch "Hello from RANCAGE" -or $RunOutput -notmatch "RANCAGE v0\.1 is running\.") {
            throw "Unexpected program output: $RunOutput"
        }

        $BytecodePath = Join-Path $TempRoot ("hello-" + [guid]::NewGuid().ToString("N") + ".rcb")
        [void](Invoke-RancageChecked -Executable $Executable -Arguments @("build", "examples\hello.cage", "-o", $BytecodePath) -Label "Bytecode build")
        $BytecodeOutput = Invoke-RancageChecked -Executable $Executable -Arguments @("run", $BytecodePath) -Label "Bytecode run"
        if ($BytecodeOutput -notmatch "Hello from RANCAGE") {
            throw "Unexpected bytecode output: $BytecodeOutput"
        }
    }
}
finally {
    if (Test-Path $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force
    }
}

Write-Host "All bundled RANCAGE smoke tests passed." -ForegroundColor Green
