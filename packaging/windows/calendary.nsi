Unicode true
RequestExecutionLevel user
SetCompressor /SOLID lzma

!ifndef VERSION
  !error "VERSION must be supplied by tools/build_windows.py"
!endif
!ifndef STAGE
  !error "STAGE must be supplied by tools/build_windows.py"
!endif
!ifndef OUTFILE
  !error "OUTFILE must be supplied by tools/build_windows.py"
!endif

!include "MUI2.nsh"

!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\Calendary"

Name "Calendary"
OutFile "${OUTFILE}"
; A fixed folder: the uninstaller removes whole subfolders and must never do that in a folder the user picked.
InstallDir "$LOCALAPPDATA\Programs\Calendary"
BrandingText "Calendary ${VERSION}"
Icon "${STAGE}\assets\icons\calendary.ico"
UninstallIcon "${STAGE}\assets\icons\calendary.ico"

VIProductVersion "${VERSION}.0"
VIAddVersionKey /LANG=1031 "ProductName" "Calendary"
VIAddVersionKey /LANG=1031 "ProductVersion" "${VERSION}"
VIAddVersionKey /LANG=1031 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=1031 "FileDescription" "Calendary Installer"
VIAddVersionKey /LANG=1031 "LegalCopyright" "MIT"

!define MUI_ICON "${STAGE}\assets\icons\calendary.ico"
!define MUI_UNICON "${STAGE}\assets\icons\calendary.ico"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\python\pythonw.exe"
!define MUI_FINISHPAGE_RUN_PARAMETERS "-m calendary"
!define MUI_FINISHPAGE_RUN_TEXT "Calendary starten"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "German"

!macro RemoveProgram
  RMDir /r "$INSTDIR\python"
  RMDir /r "$INSTDIR\src"
  RMDir /r "$INSTDIR\assets"
  Delete "$INSTDIR\google-client.json"
  Delete "$INSTDIR\LICENSE"
!macroend

Section "Calendary"
  SectionIn RO
  SetShellVarContext current
  ; an update must not keep modules or wheels the new version no longer ships
  !insertmacro RemoveProgram
  SetOutPath "$INSTDIR"
  File /r "${STAGE}\*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateShortcut "$SMPROGRAMS\Calendary.lnk" "$INSTDIR\python\pythonw.exe" "-m calendary" "$INSTDIR\assets\icons\calendary.ico" 0

  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "Calendary"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\assets\icons\calendary.ico"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "Calendary"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "${UNINSTALL_KEY}" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
  SetShellVarContext current
  ; settings, the event cache and the Credential Manager entries stay for a later reinstall
  !insertmacro RemoveProgram
  Delete "$SMPROGRAMS\Calendary.lnk"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "${UNINSTALL_KEY}"
SectionEnd
