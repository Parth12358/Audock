# Audock installer for Windows (PowerShell).
#
#   irm https://parth12358.github.io/Audock/install.ps1 | iex
#
# Installs audock.exe into %LOCALAPPDATA%\audock, adds that folder to your user PATH, and checks
# that it runs. Set $env:AUDOCK_INSTALL_DIR or $env:AUDOCK_VERSION (e.g. v0.2.0) to override.
$ErrorActionPreference = "Stop"

$repo = "Parth12358/Audock"
$dir = if ($env:AUDOCK_INSTALL_DIR) { $env:AUDOCK_INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA "audock" }
$ver = if ($env:AUDOCK_VERSION) { $env:AUDOCK_VERSION } else { "latest" }
$asset = "audock-windows-x86_64.exe"
$url = if ($ver -eq "latest") { "https://github.com/$repo/releases/latest/download/$asset" }
       else { "https://github.com/$repo/releases/download/$ver/$asset" }

New-Item -ItemType Directory -Force -Path $dir | Out-Null
$exe = Join-Path $dir "audock.exe"
Write-Host "Downloading $asset ($ver)..."
Invoke-WebRequest -Uri $url -OutFile $exe -UseBasicParsing
Unblock-File -Path $exe   # downloaded files are marked as from the internet

& $exe --help | Out-Null
if ($LASTEXITCODE -ne 0) { throw "audock: the downloaded binary did not run on this machine" }
Write-Host "Installed $exe"

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not (($userPath -split ";") -contains $dir)) {
  [Environment]::SetEnvironmentVariable("Path", (($userPath.TrimEnd(";")) + ";" + $dir).TrimStart(";"), "User")
  $env:Path = "$env:Path;$dir"
  Write-Host "Added $dir to your user PATH (new terminals pick it up automatically)."
}
Write-Host ""
Write-Host "Next, in a new or existing Obsidian vault:"
Write-Host "  audock init --dry-run   # preview; writes nothing"
Write-Host "  audock init"
