[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$PythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCommand) {
    throw 'Python was not found. Activate the project virtual environment first.'
}
$PythonExe = $PythonCommand.Source

$PyInstallerVersion = & $PythonExe -m PyInstaller --version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw 'PyInstaller is not installed in the active Python environment. Run: python -m pip install -r requirements-build.txt'
}
Write-Host "Using Python: $PythonExe" -ForegroundColor DarkGray
Write-Host "Using PyInstaller: $PyInstallerVersion" -ForegroundColor DarkGray

$DistRoot = Join-Path $Root 'dist'
$OneDirDist = Join-Path $DistRoot 'onedir'
$OneFileDist = Join-Path $DistRoot 'onefile'
$WorkRoot = Join-Path $Root '.pyinstaller-work'
$SpecRoot = Join-Path $Root '.pyinstaller-spec'
$PackageRoot = Join-Path $DistRoot 'cage-windows-x64'
$PortableRoot = Join-Path $PackageRoot 'portable'

# Remove only generated directories owned by this script.
@($OneDirDist, $OneFileDist, $WorkRoot, $SpecRoot, $PackageRoot) | ForEach-Object {
    if (Test-Path -LiteralPath $_) {
        Remove-Item -LiteralPath $_ -Recurse -Force
    }
}

New-Item -ItemType Directory -Force -Path $OneDirDist, $OneFileDist, $WorkRoot, $SpecRoot | Out-Null

$EntryPoint = Join-Path $Root 'cage_entry.py'
$SourcePath = Join-Path $Root 'src'
$ExamplePath = Join-Path $Root 'examples\hello.cage'
if (-not (Test-Path -LiteralPath $EntryPoint)) { throw "Entry point not found: $EntryPoint" }
if (-not (Test-Path -LiteralPath $ExamplePath)) { throw "Smoke-test example not found: $ExamplePath" }

$WorkOneDir = Join-Path $WorkRoot 'onedir'
$WorkOneFile = Join-Path $WorkRoot 'onefile'
$SpecOneDir = Join-Path $SpecRoot 'onedir'
$SpecOneFile = Join-Path $SpecRoot 'onefile'
New-Item -ItemType Directory -Force -Path $WorkOneDir, $WorkOneFile, $SpecOneDir, $SpecOneFile | Out-Null

Write-Host 'Building RANCAGE one-folder distribution...' -ForegroundColor Cyan
& $PythonExe -m PyInstaller `
    --noconfirm --clean --onedir --console `
    --name cage `
    --paths $SourcePath `
    --distpath $OneDirDist `
    --workpath $WorkOneDir `
    --specpath $SpecOneDir `
    $EntryPoint
if ($LASTEXITCODE -ne 0) { throw "PyInstaller one-folder build failed with exit code $LASTEXITCODE" }

Write-Host 'Building RANCAGE single-file executable...' -ForegroundColor Cyan
& $PythonExe -m PyInstaller `
    --noconfirm --clean --onefile --console `
    --name cage `
    --paths $SourcePath `
    --distpath $OneFileDist `
    --workpath $WorkOneFile `
    --specpath $SpecOneFile `
    $EntryPoint
if ($LASTEXITCODE -ne 0) { throw "PyInstaller one-file build failed with exit code $LASTEXITCODE" }

$OneDirApp = Join-Path $OneDirDist 'cage'
$OneDirExe = Join-Path $OneDirApp 'cage.exe'
$OneFileExe = Join-Path $OneFileDist 'cage.exe'
if (-not (Test-Path -LiteralPath $OneDirExe)) { throw "Expected one-folder executable not found: $OneDirExe" }
if (-not (Test-Path -LiteralPath $OneFileExe)) { throw "Expected one-file executable not found: $OneFileExe" }

New-Item -ItemType Directory -Force -Path $PackageRoot, $PortableRoot, (Join-Path $PackageRoot 'licenses') | Out-Null
Copy-Item -LiteralPath $OneFileExe -Destination (Join-Path $PackageRoot 'cage.exe') -Force
Copy-Item -Path (Join-Path $OneDirApp '*') -Destination $PortableRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $Root 'examples') -Destination $PackageRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $Root 'README-STANDALONE.md') -Destination (Join-Path $PackageRoot 'README.txt') -Force
Copy-Item -LiteralPath (Join-Path $Root 'THIRD-PARTY-NOTICES.md') -Destination (Join-Path $PackageRoot 'THIRD-PARTY-NOTICES.txt') -Force

$LicenseSource = Join-Path $Root 'licenses'
if (Test-Path -LiteralPath $LicenseSource) {
    Copy-Item -Path (Join-Path $LicenseSource '*') -Destination (Join-Path $PackageRoot 'licenses') -Recurse -Force
}
$RepositoryLicense = Join-Path $Root 'LICENSE'
if (Test-Path -LiteralPath $RepositoryLicense) {
    Copy-Item -LiteralPath $RepositoryLicense -Destination (Join-Path $PackageRoot 'LICENSE.txt') -Force
} else {
    throw 'Repository LICENSE file was not found; refusing to package without the project licensing notice.'
}

$PythonBase = (& $PythonExe -c 'import sys; print(sys.base_prefix)').Trim()
$PythonBaseExitCode = $LASTEXITCODE
if ($PythonBaseExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($PythonBase)) {
    throw 'Could not determine the active Python base installation; refusing to package without its license.'
}

$PythonLicenseCandidates = @(
    (Join-Path $PythonBase 'LICENSE.txt'),
    (Join-Path $PythonBase 'LICENSE')
)
$PythonLicense = $PythonLicenseCandidates |
    Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } |
    Select-Object -First 1
if (-not $PythonLicense) {
    throw "Python license file was not found under $PythonBase; refusing to package without it."
}
Copy-Item -LiteralPath $PythonLicense -Destination (Join-Path $PackageRoot 'licenses\PYTHON-LICENSE.txt') -Force

$PyInstallerLicenseCode = "import importlib.metadata as m; d=m.distribution('pyinstaller'); fs=d.files or []; f=next((x for x in fs if str(x).replace(chr(92), '/').split('/')[-1].lower() == 'copying.txt'), None); print(d.locate_file(f) if f else '')"
$PyInstallerLicense = (& $PythonExe -c $PyInstallerLicenseCode).Trim()
$PyInstallerLicenseExitCode = $LASTEXITCODE
if ($PyInstallerLicenseExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($PyInstallerLicense) -or -not (Test-Path -LiteralPath $PyInstallerLicense -PathType Leaf)) {
    throw 'PyInstaller COPYING.txt was not found in installed package metadata; refusing to package without the pinned build tool license notice.'
}
Copy-Item -LiteralPath $PyInstallerLicense -Destination (Join-Path $PackageRoot 'licenses\PYINSTALLER-COPYING.txt') -Force

$HooksContribLicenseCode = "import importlib.metadata as m; d=m.distribution('pyinstaller-hooks-contrib'); fs=d.files or []; f=next((x for x in fs if str(x).replace(chr(92), '/').split('/')[-1].lower() in ('license', 'license.txt')), None); print(d.locate_file(f) if f else '')"
$HooksContribLicense = (& $PythonExe -c $HooksContribLicenseCode).Trim()
$HooksContribLicenseExitCode = $LASTEXITCODE
if ($HooksContribLicenseExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($HooksContribLicense) -or -not (Test-Path -LiteralPath $HooksContribLicense -PathType Leaf)) {
    throw 'pyinstaller-hooks-contrib LICENSE was not found in installed package metadata; refusing to package without its third-party license notice.'
}
Copy-Item -LiteralPath $HooksContribLicense -Destination (Join-Path $PackageRoot 'licenses\PYINSTALLER-HOOKS-CONTRIB-LICENSE.txt') -Force
function Test-RancageExecutable {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Example
    )

    if (-not (Test-Path -LiteralPath $Executable)) { throw "$Label executable is missing: $Executable" }

    Write-Host "Smoke-testing ${Label}: --version" -ForegroundColor Cyan
    $VersionOutput = @(& $Executable --version 2>&1)
    $VersionExitCode = $LASTEXITCODE
    if ($VersionExitCode -ne 0) { throw "$Label --version failed with exit code $VersionExitCode" }
    $VersionText = $VersionOutput -join "`n"
    if ($VersionText -notmatch 'RANCAGE\s+\S+') { throw "$Label returned an unexpected version output: $VersionText" }
    Write-Host $VersionText

    Write-Host "Smoke-testing ${Label}: hello.cage" -ForegroundColor Cyan
    $RunOutput = @(& $Executable run $Example 2>&1)
    $RunExitCode = $LASTEXITCODE
    if ($RunExitCode -ne 0) { throw "$Label hello-world execution failed with exit code $RunExitCode" }
    $RunText = $RunOutput -join "`n"
    if ($RunText -notmatch 'Hello from RANCAGE' -or $RunText -notmatch 'RANCAGE v0\.1 is running\.') {
        throw "$Label returned unexpected program output: $RunText"
    }
    Write-Host $RunText
}

$StandaloneExe = Join-Path $DistRoot 'cage-windows-x64.exe'
Copy-Item -LiteralPath $OneFileExe -Destination $StandaloneExe -Force
$PortableExe = Join-Path $PortableRoot 'cage.exe'

# Verify both executables before packaging them.
Test-RancageExecutable -Executable $StandaloneExe -Label 'one-file' -Example $ExamplePath
Test-RancageExecutable -Executable $PortableExe -Label 'one-folder portable' -Example $ExamplePath

# Use Windows tar.exe instead of Compress-Archive. tar.exe avoids the ZIP
# helper's occasional file-sharing conflict observed on some Windows systems.
$TarCommand = Get-Command tar.exe -ErrorAction SilentlyContinue
if (-not $TarCommand) { throw 'tar.exe was not found. It is required to create the portable ZIP archive.' }
$TarExe = $TarCommand.Source
$ZipPath = Join-Path $DistRoot 'cage-windows-x64.zip'
$ArchiveCreated = $false

for ($Attempt = 1; $Attempt -le 3; $Attempt++) {
    if (Test-Path -LiteralPath $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }

    Write-Host "Creating portable ZIP (attempt $Attempt of 3)..." -ForegroundColor Cyan
    & $TarExe -a -c -f $ZipPath -C $PackageRoot .
    $TarExitCode = $LASTEXITCODE

    if ($TarExitCode -eq 0 -and (Test-Path -LiteralPath $ZipPath) -and (Get-Item -LiteralPath $ZipPath).Length -gt 0) {
        $ArchiveCreated = $true
        break
    }

    if ($Attempt -lt 3) {
        Write-Warning "ZIP creation attempt $Attempt failed (exit code $TarExitCode); retrying."
        Start-Sleep -Seconds 2
    }
}

if (-not $ArchiveCreated) { throw 'Portable ZIP creation failed after 3 attempts. No successful build is reported.' }

Write-Host 'Validating portable ZIP contents...' -ForegroundColor Cyan
$ArchiveListing = @(& $TarExe -tf $ZipPath 2>&1)
if ($LASTEXITCODE -ne 0) { throw 'The generated ZIP could not be listed; archive validation failed.' }
$ArchiveListingText = $ArchiveListing -join "`n"
if ($ArchiveListingText -notmatch '(?m)(^|/)cage\.exe$') { throw 'The generated ZIP does not contain the root cage.exe.' }
if ($ArchiveListingText -notmatch '(?m)(^|/)portable/cage\.exe$') { throw 'The generated ZIP does not contain portable/cage.exe.' }
$RequiredArchiveFiles = @(
    'LICENSE.txt',
    'THIRD-PARTY-NOTICES.txt',
    'licenses/CORE-PROPRIETARY.txt',
    'licenses/SDK-MIT.txt',
    'licenses/PYTHON-LICENSE.txt',
    'licenses/PYINSTALLER-COPYING.txt',
    'licenses/PYINSTALLER-HOOKS-CONTRIB-LICENSE.txt'
)

foreach ($RequiredFile in $RequiredArchiveFiles) {
    $Pattern = '(?m)(^|/)' + [regex]::Escape($RequiredFile) + '$'

    if ($ArchiveListingText -notmatch $Pattern) {
        throw "The generated ZIP is missing required license notice: $RequiredFile"
    }
}

Write-Host 'All required license notices are present in the ZIP.' -ForegroundColor Green

$HashLines = @(
    "SHA256  cage-windows-x64.exe  $((Get-FileHash -LiteralPath $StandaloneExe -Algorithm SHA256).Hash)",
    "SHA256  cage-windows-x64.zip  $((Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash)"
)
$HashPath = Join-Path $DistRoot 'SHA256SUMS.txt'
$HashLines | Set-Content -LiteralPath $HashPath -Encoding ascii

Write-Host ''
Write-Host 'RANCAGE standalone build and smoke tests completed successfully:' -ForegroundColor Green
Write-Host "  $StandaloneExe"
Write-Host "  $ZipPath"
Write-Host "  $HashPath"
