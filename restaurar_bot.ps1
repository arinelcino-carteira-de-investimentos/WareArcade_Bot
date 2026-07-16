# WareArcadeBot - Launcher (ASCII-only)
# Este arquivo apenas chama o instalador Python.
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)
Write-Host "WareArcadeBot - Iniciando instalador Python..." -ForegroundColor Cyan
$py = "python"
try { & $py --version 2>&1 | Out-Null } catch {
    try { $py = "py"; & $py --version 2>&1 | Out-Null } catch {
        Write-Host "Python nao encontrado. Instale em https://python.org" -ForegroundColor Red
        Read-Host "Pressione ENTER"
        exit 1
    }
}
& $py "$PSScriptRoot\instalar.py"
