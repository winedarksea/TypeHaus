# Type:Haus bootstrapper for Windows PowerShell.
# Usage:  irm https://type-house.com/install.ps1 | iex
$ErrorActionPreference = "Stop"

function Info($m) { Write-Host "==> $m" -ForegroundColor Cyan }

# 1. Find Python 3.11+
$py = $null
foreach ($cand in @("python", "python3", "py")) {
  $exe = Get-Command $cand -ErrorAction SilentlyContinue
  if ($exe) {
    $ok = & $exe.Source -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) { $py = $exe.Source; break }
  }
}
if (-not $py) { throw "Python 3.11+ is required. Install it from https://python.org and re-run." }
Info "Using $(& $py --version)"

# 2. Ensure pipx
if (-not (Get-Command pipx -ErrorAction SilentlyContinue)) {
  Info "Installing pipx for the current user..."
  & $py -m pip install --user --quiet pipx
  & $py -m pipx ensurepath | Out-Null
}

# 3. Install Type:Haus (with the server extras for `haus serve`)
Info "Installing typehaus[server] ..."
& $py -m pipx install --force "typehaus[server]"

Write-Host ""
Write-Host "Type:Haus is installed."
Write-Host "  New house:  haus new my-house"
Write-Host "  Edit:       haus serve my-house   (http://127.0.0.1:8000)"
Write-Host "  Browser:    https://type-house.com/app"
Write-Host "  Uninstall:  pipx uninstall typehaus"
