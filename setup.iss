[Setup]
AppName=Danny Capture
AppVersion=1.0
AppPublisher=Danny Inc.
DefaultDirName={autopf}\Danny Capture
DefaultGroupName=Danny Capture
OutputDir=installer
OutputBaseFilename=DannyCapture_Setup
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=compiler:SetupClassicIcon.ico

[Tasks]
Name: "desktopicon"; Description: "바탕화면에 바로가기 아이콘 만들기"; GroupDescription: "추가 작업:"; Flags: unchecked

[Files]
Source: "dist\DannyCapture\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Danny Capture"; Filename: "{app}\DannyCapture.exe"
Name: "{autodesktop}\Danny Capture"; Filename: "{app}\DannyCapture.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\DannyCapture.exe"; Description: "Danny Capture 실행"; Flags: nowait postinstall skipifsilent
