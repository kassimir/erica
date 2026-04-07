# Erica Shell (WinUI 3)

Implements the **shell layer** from [`../ERICA_ARCHITECTURE.md`](../ERICA_ARCHITECTURE.md): chromeless full-screen host, **no embedded LLM** (thin HTTP client to the agent), command palette, Quake console, status bar (connection + persona mode), and configurable agent base URL.

| Architecture requirement | Implementation |
|-------------------------|----------------|
| Borderless / full-screen | `AppWindowPresenterKind.FullScreen`, dark `RequestedTheme` |
| Command palette `Ctrl+Space` | `PaletteOverlay` → `CommandRouter` → agent `POST /execute` |
| Quake `Ctrl+`` | Top overlay, `CompositeTransform.TranslateY` slide animation, stream via `/execute/stream` |
| Status bar | `Agent: online/offline`, `Mode:` from `GET /health`, activity line, shortcut hint |
| Configuration | [`appsettings.json`](appsettings.json) `EriCAShell.AgentBaseUrl` |

## Architecture (code layout)

| Piece | Role |
|--------|------|
| [`App.xaml.cs`](App.xaml.cs) | Application entry; calls [`ShellAppHost.Initialize()`](ShellAppHost.cs). |
| [`ShellAppHost.cs`](ShellAppHost.cs) | Loads [`appsettings.json`](appsettings.json), logging, [`AgentClient`](Services/AgentClient.cs), [`CopilotApiClient`](Services/CopilotApiClient.cs), [`VoiceInputHandler`](Services/VoiceInputHandler.cs), [`CommandRouter`](Services/CommandRouter.cs). |
| [`CommandRouter`](Services/CommandRouter.cs) | Routes text: default → agent `/execute` or `/execute/stream`; `copilot:` → OpenAI-style chat (if configured); `voice:` → voice stub. |
| [`CopilotApiClient`](Services/CopilotApiClient.cs) | Bearer token + JSON to a chat-completions endpoint (Azure OpenAI / OpenAI / gateway). |
| [`VoiceInputHandler`](Services/VoiceInputHandler.cs) | Placeholder + optional POST to agent `/voice/stt`. |
| [`Logging/ShellLogging.cs`](Logging/ShellLogging.cs) | `Debug.WriteLine` with configurable minimum level. |
| [`appsettings.json`](appsettings.json) | `EriCAShell` section: `AgentBaseUrl`, `Copilot`, `Logging`. |

## Build

Requires Visual Studio 2022 with the **Windows application development** workload and **Windows App SDK** / WinUI 3 templates.

Open [`../Erica.sln`](../Erica.sln), build **Erica.Shell** (x64).

## Run

1. Start the agent (see [`../agent/README.md`](../agent/README.md)).
2. Run `Erica.Shell.exe` from the build output directory (`appsettings.json` is copied next to the exe).

Configure URLs and API keys in **`appsettings.json`** (not committed secrets—use user secrets or env in production).
