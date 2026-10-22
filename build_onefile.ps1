# 单文件绿色版：整个程序（含 _internal 里的运行时）塞进一个 exe。
# 不修改 build_win.ps1；产物与 onedir 版并存。
# 产物：dist\pdf-office-toolkit-onefile.exe
#
# 代价：
#   - 每次启动先把内容解压到 %TEMP%\_MEIxxxx，冷启动比 onedir 慢 1～3 秒；
#   - 体积只比 onedir 略小，杀软对 onefile 的误报概率更高；
#   - 运行期间会占用一份临时目录，退出后 PyInstaller 自动清理。
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

$running = Get-Process -Name pdf-office-toolkit, pdf-office-toolkit-onefile -ErrorAction SilentlyContinue
if ($running) {
  throw "检测到程序正在运行（PID: $($running.Id -join ', ')），请先关闭。"
}

pyinstaller --noconfirm --clean --onefile --windowed --name pdf-office-toolkit-onefile `
  --collect-all customtkinter --collect-all pypdfium2 `
  --collect-all tkinterdnd2 `
  --collect-data pdf_gui --paths src `
  --hidden-import PIL._tkinter_finder `
  run_pdf_gui.py

$exe = "dist\pdf-office-toolkit-onefile.exe"
if (-not (Test-Path $exe)) {
  throw "构建完成但未找到 $exe。"
}
$size = (Get-Item $exe).Length / 1MB
Write-Host ("完成：{0}（{1:N1} MB）" -f $exe, $size)
Write-Host "双击这一个 exe 即可运行，不需要 _internal 目录。"
