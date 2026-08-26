flet pack main.py `
    --name chord_box `
    --icon chord_box/chord_box.ico `
    --onedir `
    --add-data "chord_box/query/harmony.pl;chord_box/query" `
    --add-data "chord_box/chord_box.ico;chord_box" `
    --hidden-import pyswip `
    --hidden-import pychord `
    --hidden-import pretty_midi `
    --hidden-import pillow `
    --hidden-import PIL `
    --hidden-import pystray `
    --hidden-import chord_box `
    --product-name "chord_box" `
    --product-version "1.3.0" `
    --company-name "Anakah"

Remove-Item chord_box.spec -Force -ErrorAction SilentlyContinue
Remove-Item build -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "按任意键继续..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

