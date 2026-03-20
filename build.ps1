# Script para construir el ejecutable
Write-Host "Instalando dependencias necesarias para build..."
pip install pyinstaller

Write-Host "Construyendo ejecutable con PyInstaller..."
pyinstaller --noconfirm --onedir --windowed --name "SupeRois" --icon "icon.ico" --hidden-import "keyboard" --hidden-import "pygame" --hidden-import "vgamepad" main.py

$releaseFolder = "C:\Users\Lauta\Desktop\SupeRois_Release"

Write-Host "Creando carpeta de release en el Escritorio: $releaseFolder"
if (Test-Path $releaseFolder) {
    Remove-Item -Recurse -Force $releaseFolder
}
New-Item -ItemType Directory -Force -Path $releaseFolder | Out-Null

Write-Host "Copiando binarios y dependencias..."
Copy-Item -Recurse -Force "dist\SupeRois\*" $releaseFolder\

Write-Host "Copiando carpetas Data y Config..."
Copy-Item -Recurse -Force "config" $releaseFolder\
Copy-Item -Recurse -Force "data" $releaseFolder\
Copy-Item -Force "README.txt" $releaseFolder\

Write-Host "Moviendo el script a la papelera..."
Write-Host "COMPLETADO"
Copy-Item -Force "README.txt" $releaseFolder\
