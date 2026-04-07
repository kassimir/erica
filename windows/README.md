# Windows API layer

- **`Erica.Windows`** — C# class library with P/Invoke wrappers for window enumeration, titles, focus, minimize, move/resize, and process launch helpers.
- **`Erica.Windows.Cli`** — JSON-over-stdin console used by Python skills when `ERICA_WINDOWS_CLI` points to `Erica.Windows.Cli.exe`.

Build with Visual Studio from [`../Erica.sln`](../Erica.sln) (x64).

Example (PowerShell):

```powershell
$json = '{"target":"notepad"}'
$json | & .\Erica.Windows.Cli\bin\x64\Release\net8.0-windows10.0.19041.0\Erica.Windows.Cli.exe launch
```

Wire the output path into the agent environment variable `ERICA_WINDOWS_CLI`.
