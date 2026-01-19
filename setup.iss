; Скрипт Inno Setup для создания инсталлятора Chatlist
; Версия должна быть обновлена вручную или через build_installer.bat

#define AppName "Chatlist"
#define AppPublisher "Chatlist Application"
#define AppURL "https://github.com/yourusername/chatlist"
#define AppExeName "PyQtApp.exe"
#define AppVersion "1.0.1"

[Setup]
; Основные настройки
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=installer
OutputBaseFilename=Chatlist-Setup-{#AppVersion}
SetupIconFile=app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#AppExeName}

; Языки
[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

; Задачи
[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

; Файлы для установки
[Files]
; Основной исполняемый файл
Source: "dist\PyQtApp.exe"; DestDir: "{app}"; DestName: "{#AppExeName}"; Flags: ignoreversion

; Иконка приложения (если есть)
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion; Check: FileExists(ExpandConstant('{src}\app.ico'))

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\app.ico"; Check: FileExists(ExpandConstant('{app}\app.ico'))
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Check: not FileExists(ExpandConstant('{app}\app.ico'))
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; IconFilename: "{app}\app.ico"; Check: FileExists(ExpandConstant('{app}\app.ico'))
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; Check: not FileExists(ExpandConstant('{app}\app.ico'))
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon; IconFilename: "{app}\app.ico"; Check: FileExists(ExpandConstant('{app}\app.ico'))
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon; Check: not FileExists(ExpandConstant('{app}\app.ico'))

; Реестр
[Registry]
; Добавляем в реестр для корректной работы деинсталляции
Root: HKCU; Subkey: "Software\{#AppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; Flags: uninsdeletevalue
Root: HKCU; Subkey: "Software\{#AppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#AppVersion}"; Flags: uninsdeletekey

; Секция деинсталляции
[UninstallDelete]
; Удаляем все файлы приложения (включая базу данных и логи, если они в папке установки)
Type: filesandordirs; Name: "{app}"
; Удаляем базу данных из папки установки
Type: files; Name: "{app}\chatlist.db"
; Удаляем папку с логами
Type: filesandordirs; Name: "{app}\logs"

; Код для деинсталляции
[Code]
function InitializeSetup(): Boolean;
var
  UserDataPath: String;
  EnvExamplePath: String;
begin
  // Создаем папку пользовательских данных
  UserDataPath := ExpandConstant('{localappdata}\Chatlist');
  if not DirExists(UserDataPath) then
    CreateDir(UserDataPath);
  
  // Копируем .env.example если существует
  EnvExamplePath := UserDataPath + '\.env.example';
  if FileExists(ExpandConstant('{src}\.env.example')) then
    CopyFile(ExpandConstant('{src}\.env.example'), EnvExamplePath, False);
  
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserDataPath: String;
  LogsPath: String;
  DatabasePath: String;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Получаем путь к папке пользовательских данных
    UserDataPath := ExpandConstant('{localappdata}\Chatlist');
    LogsPath := UserDataPath + '\logs';
    DatabasePath := UserDataPath + '\chatlist.db';
    
    // Удаляем базу данных (если пользователь хочет сохранить данные, он может отменить деинсталляцию)
    if FileExists(DatabasePath) then
      DeleteFile(DatabasePath);
    
    // Удаляем логи
    if DirExists(LogsPath) then
      DelTree(LogsPath, True, True, True);
    
    // Удаляем папку пользовательских данных, если она пуста
    if DirExists(UserDataPath) then
      RemoveDir(UserDataPath);
  end;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
  // Можно добавить проверку, запущено ли приложение
  // и предложить пользователю закрыть его
end;

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
