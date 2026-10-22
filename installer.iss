; Inno Setup 6 安装包脚本。
; 构建：.\build_installer.ps1（会先调用 build_win.ps1 生成绿色版，再编译本脚本）
; 产物：dist\pdf-office-toolkit-setup-x64.exe
;
; 中文安装界面（可选）：把 ChineseSimplified.isl 放到本文件同目录，
; 编译时会自动多出一个中文语言选项；没有则只用英文界面。

#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{B7E5A1C3-4D2F-4A88-9B61-2F0C7E5D3A94}
AppName=PDF 办公百宝箱
AppVerName=PDF 办公百宝箱 {#AppVersion}
AppVersion={#AppVersion}
AppPublisher=魔都吴所谓
AppPublisherURL=https://github.com/moduwusuowei/pdf-office-toolkit
AppSupportURL=https://github.com/moduwusuowei/pdf-office-toolkit/issues
AppUpdatesURL=https://github.com/moduwusuowei/pdf-office-toolkit/releases
DefaultDirName={autopf}\PDF Office Toolkit
DefaultGroupName=PDF 办公百宝箱
DisableProgramGroupPage=yes
OutputDir=dist
OutputBaseFilename=pdf-office-toolkit-setup-x64
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; admin：装到 Program Files；安装向导里允许用户改成“仅为我安装”（免 UAC）
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\pdf-office-toolkit.exe
VersionInfoVersion={#AppVersion}
; 程序正在运行时提示关闭，而不是装满一半报占用
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
#if FileExists(AddBackslash(SourcePath) + "ChineseSimplified.isl")
Name: "chinesesimplified"; MessagesFile: "ChineseSimplified.isl"
#endif

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\pdf-office-toolkit\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\PDF 办公百宝箱"; Filename: "{app}\pdf-office-toolkit.exe"
Name: "{group}\{cm:UninstallProgram,PDF 办公百宝箱}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\PDF 办公百宝箱"; Filename: "{app}\pdf-office-toolkit.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\pdf-office-toolkit.exe"; Description: "{cm:LaunchProgram,PDF 办公百宝箱}"; Flags: nowait postinstall skipifsilent
