using System.Text.Json.Serialization;

namespace Erica.Shell.Config;

public sealed class ShellSettingsRoot
{
    [JsonPropertyName("EriCAShell")]
    public EriCAShellSection EriCAShell { get; init; } = new();
}

public sealed class EriCAShellSection
{
    public string AgentBaseUrl { get; init; } = "http://127.0.0.1:8742";
    /// <summary><c>FullScreen</c> (default) or <c>Windowed</c> for dev/debug with custom chrome strip.</summary>
    public string WindowMode { get; init; } = "FullScreen";
    public CopilotSection Copilot { get; init; } = new();
    public LoggingSection Logging { get; init; } = new();
}

public sealed class CopilotSection
{
    public bool Enabled { get; init; }
    public string Endpoint { get; init; } = "";
    public string ApiKey { get; init; } = "";
    public string Model { get; init; } = "gpt-4o-mini";
    public string SystemPrompt { get; init; } = "";
}

public sealed class LoggingSection
{
    public string MinimumLevel { get; init; } = "Information";
}
