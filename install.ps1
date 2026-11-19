# ============================================================
#  IT-aanhuis Helpdesk AI - Windows installatie (PowerShell)
#  Installeert Python-dependencies, optioneel Ollama (winget) en
#  haalt het standaard base-model op.
#
#  Draai vanuit deze map:
#     powershell -ExecutionPolicy Bypass -File .\install.ps1
# ============================================================
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

function Info($m){ Write-Host "[~] $m" -ForegroundColor Cyan }
function Ok($m){   Write-Host "[OK] $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[!] $m" -ForegroundColor Yellow }

Write-Host ""
Write-Host "  IT-AANHUIS Helpdesk AI  //  Windows installatie" -ForegroundColor Cyan
Write-Host ""

# Python
$py = $null
foreach ($c in @("py","python")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break }
}
if (-not $py) {
    Warn "Python niet gevonden. Installeer Python 3.9+ via https://python.org of: winget install Python.Python.3.12"
    exit 1
}
Ok "Python gevonden: $py"

Info "Python-dependencies installeren (customtkinter, Pillow)..."
& $py -m pip install --upgrade pip | Out-Null
& $py -m pip install -r requirements.txt
Ok "Dependencies klaar"

# Ollama
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Ok "Ollama al geinstalleerd"
} else {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Info "Ollama installeren via winget..."
        try { winget install -e --id Ollama.Ollama --silent --accept-package-agreements --accept-source-agreements } catch { Warn "winget mislukt - download via https://ollama.com/download" }
    } else {
        Warn "Installeer Ollama via https://ollama.com/download en draai dit script opnieuw."
    }
}

# standaard model
if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Info "Standaard base-model ophalen: qwen2.5-coder:1.5b-base"
    try { ollama pull qwen2.5-coder:1.5b-base } catch { Warn "Download mislukt - je kunt het model later installeren in de app." }
}

Write-Host ""
Ok "Klaar. Start met:  .\run.bat"
Write-Host ""
