[Setup]
AppName=Danny Capture
AppVersion=1.1.0
VersionInfoVersion=1.1.0.0
AppPublisher=Ninetynine Inc.
AppPublisherURL=https://ninetynine99.co.kr
AppSupportURL=https://ninetynine99.co.kr/contact
AppContact=bignine99@naver.com
AppCopyright=Copyright (C) 2026 Ninetynine Inc.
DefaultDirName={localappdata}\DannyCapture
DefaultGroupName=Danny Capture
OutputBaseFilename=DannyCapture_Setup
OutputDir=Output
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\icon.ico
UninstallDisplayName=Danny Capture (Ninetynine Inc.)

[Files]
; Nuitka standalone distribution (entire folder)
Source: "nuitka_build\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\Danny Capture"; Filename: "{app}\DannyCapture.exe"; IconFilename: "{app}\icon.ico"
Name: "{userprograms}\Danny Capture"; Filename: "{app}\DannyCapture.exe"; IconFilename: "{app}\icon.ico"
Name: "{userprograms}\Uninstall Danny Capture"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\DannyCapture.exe"; Description: "Danny Capture 실행"; Flags: nowait postinstall skipifsilent
