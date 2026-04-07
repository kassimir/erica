# Windows API layer (`Erica.Windows`)

C# **P/Invoke** interop aligned with [`../ERICA_ARCHITECTURE.md`](../ERICA_ARCHITECTURE.md): window enumeration, titles, class names, bounds, focus, minimize / maximize / restore, placement, move/resize, and process launch.

## Library (`Erica.Windows`)

| Type | Role |
|------|------|
| [`NativeMethods.cs`](Erica.Windows/NativeMethods.cs) | `user32.dll` / `kernel32.dll` declarations: `RECT`, `POINT`, `WINDOWPLACEMENT`, `EnumWindows`, `GetWindowText`, `GetClassNameW`, `ShowWindow`, `GetWindowPlacement`, `MoveWindow`, `AttachThreadInput`, `AllowSetForegroundWindow`, etc. |
| [`WindowRect.cs`](Erica.Windows/WindowRect.cs) | Public screen-space bounds. |
| [`WindowDescriptor.cs`](Erica.Windows/WindowDescriptor.cs) | Handle + title + bounds + class name for enumeration. |
| [`WindowPlacementInfo.cs`](Erica.Windows/WindowPlacementInfo.cs) | Public subset of `WINDOWPLACEMENT`. |
| [`WindowService.cs`](Erica.Windows/WindowService.cs) | `ListVisibleWindows`, `FindVisibleWindowByTitleSubstring`, `TrySetForegroundWindow`, `MaximizeWindow` / `RestoreWindow` / `MinimizeWindow`, `MoveResize`, `TryGetWindowPlacementInfo`, … |
| [`ProcessLauncher.cs`](Erica.Windows/ProcessLauncher.cs) | `TryStart` / `StartProcess` via shell execute. |

## CLI (`Erica.Windows.Cli`)

JSON on **stdin**, JSON on **stdout** (camelCase). Used by Python skills when `ERICA_WINDOWS_CLI` is set.

Examples (PowerShell):

```powershell
'{"target":"notepad"}' | .\Erica.Windows.Cli.exe launch
'{"foreground":true}' | .\Erica.Windows.Cli.exe window_maximize
'{}' | .\Erica.Windows.Cli.exe window_list
'{"handle":123456}' | .\Erica.Windows.Cli.exe window_placement
```

Build from [`../Erica.sln`](../Erica.sln) (x64). Wi-Fi and default audio device switches remain **stubs** here; implement via dedicated APIs or skills if you need production behavior.
