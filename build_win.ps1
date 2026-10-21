# 构建 Windows 绿色版（onedir）并压缩为 zip。
# 产物：dist\pdf-office-toolkit\（双击 exe 运行）、dist\pdf-office-toolkit-windows-x64.zip
$ErrorActionPreference = "Stop"

pyinstaller --noconfirm --clean --onedir --windowed --name pdf-office-toolkit `
  --collect-all customtkinter --collect-all pypdfium2 `
  --collect-data pdf_gui `
  --hidden-import PIL._tkinter_finder `
  src/pdf_gui/main.py

Compress-Archive -Path dist\pdf-office-toolkit -DestinationPath dist\pdf-office-toolkit-windows-x64.zip

Write-Host "完成：dist\pdf-office-toolkit-windows-x64.zip"
