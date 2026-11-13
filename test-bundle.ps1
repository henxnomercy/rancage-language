[CmdletBinding()]
param(
    [string]$OneFileExe = "dist\onefile\nova.exe",
    [string]$OneDirExe = "dist\onedir\nova\nova.exe"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Invoke-NovaChecked {
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

$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "nova-bundle-smoke-$PID"
New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null

try {
    foreach ($Executable in $Executables) {
        Write-Host "Smoke-testing $Executable" -ForegroundColor Cyan

        $Version = Invoke-NovaChecked -Executable $Executable -Arguments @("--version") -Label "Version check"
        if ($Version -notmatch "NOVA 0\.2\.0a1") {
            throw "Unexpected NOVA version: $Version"
        }

        [void](Invoke-NovaChecked -Executable $Executable -Arguments @("check", "examples\hello.nova") -Label "Source check")

        $RunOutput = Invoke-NovaChecked -Executable $Executable -Arguments @("run", "examples\hello.nova") -Label "Source run"
        if ($RunOutput -notmatch "Hello from NOVA" -or $RunOutput -notmatch "NOVA v0\.1 is running\.") {
            throw "Unexpected program output: $RunOutput"
        }

        $BytecodePath = Join-Path $TempRoot ("hello-" + [guid]::NewGuid().ToString("N") + ".nvm")
        [void](Invoke-NovaChecked -Executable $Executable -Arguments @("build", "examples\hello.nova", "-o", $BytecodePath) -Label "Bytecode build")
        $BytecodeOutput = Invoke-NovaChecked -Executable $Executable -Arguments @("run", $BytecodePath) -Label "Bytecode run"
        if ($BytecodeOutput -notmatch "Hello from NOVA") {
            throw "Unexpected bytecode output: $BytecodeOutput"
        }
    }
}
finally {
    if (Test-Path $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force
    }
}

Write-Host "All bundled NOVA smoke tests passed." -ForegroundColor Green
