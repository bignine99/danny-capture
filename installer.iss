[Setup]
AppName=Danny Capture
AppVersion=1.0.0
VersionInfoVersion=1.0.0.0
AppPublisher=Ninetynine Inc.
AppPublisherURL=https://ninetynine99.co.kr
AppSupportURL=https://ninetynine99.co.kr/contact
AppContact=bignine99@naver.com
AppCopyright=Copyright (C) 2026 Ninetynine Inc.
DefaultDirName={localappdata}\DannyCapture
DefaultGroupName=Danny Capture
OutputBaseFilename=DannyCapture_Setup
OutputDir=Output
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
AppMutex=DannyCapture_SingleInstance
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\icon.ico
UninstallDisplayName=Danny Capture (Ninetynine Inc.)
; Signing command (requires signtool to be configured)
; SignTool=signtool sign /f "$qcert.pfx$q" /p "$qpassword$q" /t http://timestamp.digicert.com $f

[Files]
; You can include either the single EXE or the directory. Here we assume the single EXE.
Source: "dist\DannyCapture_Single.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\Danny Capture"; Filename: "{app}\DannyCapture_Single.exe"; IconFilename: "{app}\icon.ico"
; Creates the start menu icon
Name: "{userprograms}\Danny Capture"; Filename: "{app}\DannyCapture_Single.exe"; IconFilename: "{app}\icon.ico"
Name: "{userprograms}\Uninstall Danny Capture"; Filename: "{uninstallexe}"
