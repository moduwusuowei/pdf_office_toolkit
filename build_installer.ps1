# 生成带安装向导的 setup.exe（安装版）。
# 不修改 build_win.ps1：本脚本复用它的绿色版产物，再交给 Inno Setup 编译。
# 产物：dist\pdf-office-toolkit-setup-x64.exe
#
# 用法：
#   .\build_installer.ps1                # 完整构建（PyInstaller + Inno Setup）
#   .\build_installer.ps1 -SkipBuild     # 复用 dist\pdf-office-toolkit，只重新编译安装包
param(
  [switch]$SkipBuild
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

# 绿色版正在运行时，dist\_internal 会被占用，PyInstaller 和安装包编译都会失败
$running = Get-Process -Name pdf-office-toolkit -ErrorAction SilentlyContinue
if ($running) {
  throw "检测到 pdf-office-toolkit 正在运行（PID: $($running.Id -join ', ')），请先关闭程序。"
}

# 找 Inno Setup 6 的编译器（PATH 里没有就找默认安装目录）
$candidates = @()
$cmd = Get-Command iscc -ErrorAction SilentlyContinue
if ($cmd) { $candidates += $cmd.Source }
$candidates += @(
  "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
  "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)
$iscc = $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $iscc) {
  throw "未找到 Inno Setup 6（ISCC.exe）。安装方式：winget install JRSoftware.InnoSetup 或 choco install innosetup -y"
}

# 版本号唯一来源：src\pdf_gui\gui\app_meta.json
$meta = Get-Content "src\pdf_gui\gui\app_meta.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$version = [string]$meta.version
if ($version -notmatch '^\d+\.\d+\.\d+') {
  throw "app_meta.json 里的 version 不是 x.y.z：$version"
}

if (-not $SkipBuild) {
  & "$PSScriptRoot\build_win.ps1"
} elseif (-not (Test-Path "dist\pdf-office-toolkit\pdf-office-toolkit.exe")) {
  throw "dist 里没有绿色版，去掉 -SkipBuild 先构建一次。"
}

& $iscc "/DAppVersion=$version" "installer.iss"
if ($LASTEXITCODE -ne 0) {
  throw "Inno Setup 编译失败（退出码 $LASTEXITCODE）"
}

$setup = "dist\pdf-office-toolkit-setup-x64.exe"
if (-not (Test-Path $setup)) {
  throw "编译完成但未找到 $setup，请检查 installer.iss 的 OutputDir。"
}
$size = (Get-Item $setup).Length / 1MB
Write-Host ("完成：{0}（{1:N1} MB，版本 {2}）" -f $setup, $size, $version)
