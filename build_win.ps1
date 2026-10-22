# 构建 Windows 绿色版（onedir）并压缩为 zip。
# 产物：dist\pdf-office-toolkit\（双击 exe 运行）、dist\pdf-office-toolkit-windows-x64.zip
$ErrorActionPreference = "Stop"

# 绿色版正在运行时，dist\_internal\base_library.zip 被占用：
# PyInstaller 覆盖失败，Compress-Archive 也会报“正由另一进程使用”。
$running = Get-Process -Name pdf-office-toolkit -ErrorAction SilentlyContinue
if ($running) {
  throw "检测到 pdf-office-toolkit 正在运行（PID: $($running.Id -join ', ')），请先关闭程序再打包。"
}

pyinstaller --noconfirm --clean --onedir --windowed --name pdf-office-toolkit `
  --collect-all customtkinter --collect-all pypdfium2 `
  --collect-data pdf_gui `
  --hidden-import PIL._tkinter_finder `
  --collect-all tkinterdnd2 `
  --paths src `
  run_pdf_gui.py

# 上次失败可能留下半截 zip，先删掉再压
$zip = "dist\pdf-office-toolkit-windows-x64.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path dist\pdf-office-toolkit -DestinationPath $zip

Write-Host "完成：$zip"
Write-Host "运行请双击：dist\pdf-office-toolkit\pdf-office-toolkit.exe（build\ 下的是中间文件，缺 _internal，不能直接运行）"
