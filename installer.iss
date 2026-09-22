[Setup]
AppName=Albedolizer
AppVersion=1.7.2-beta
AppVerName=Albedolizer 1.7.2-beta
AppPublisher=INV.LVL
AppPublisherURL=https://github.com/invisiblelevel/Albedolizer
DefaultDirName={autopf}\Albedolizer
DefaultGroupName=Albedolizer
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=Albedolizer_Setup_v1.7.2-beta
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\Albedolizer.exe
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\Albedolizer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\viewer.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\autolevels.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\free_xcittiny_wa14.onnx"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\lutwithbgrid_fivek.onnx"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\clip_vision_int8.onnx"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\clip_text_encoder.onnx"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\clip_tokenizer\*"; DestDir: "{app}\clip_tokenizer"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "dist\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\manual.html"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\env.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\env_blur.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\screenshots\*"; DestDir: "{app}\screenshots"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Albedolizer"; Filename: "{app}\Albedolizer.exe"
Name: "{group}\{cm:UninstallProgram,Albedolizer}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Albedolizer"; Filename: "{app}\Albedolizer.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Albedolizer.exe"; Description: "{cm:LaunchProgram,Albedolizer}"; Flags: nowait postinstall skipifsilent