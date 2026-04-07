using Erica.Shell.Logging;

namespace Erica.Shell.Services;

public enum CommandTarget
{
    AgentExecute,
    AgentStream,
    CopilotChat,
    VoiceStub
}

public sealed class RoutedCommandResult
{
    public CommandTarget Target { get; init; }
    public string Output { get; init; } = "";
}

/// <summary>
/// Routes user text to the local agent, optional Copilot-compatible API, or voice placeholder.
/// Prefixes: <c>copilot:</c> (if enabled), <c>voice:</c> stub.
/// </summary>
public sealed class CommandRouter
{
    private readonly AgentClient _agent;
    private readonly CopilotApiClient _copilot;
    private readonly VoiceInputHandler _voice;
    private readonly ShellLogger _log;

    public CommandRouter(AgentClient agent, CopilotApiClient copilot, VoiceInputHandler voice, ShellLogger log)
    {
        _agent = agent;
        _copilot = copilot;
        _voice = voice;
        _log = log;
    }

    public async Task<RoutedCommandResult> RouteAsync(
        string text,
        bool streamToAgent,
        CancellationToken cancellationToken = default)
    {
        var t = text.Trim();
        if (t.StartsWith("voice:", StringComparison.OrdinalIgnoreCase))
        {
            _ = await _voice.TranscribePlaceholderAsync(cancellationToken);
            return new RoutedCommandResult { Target = CommandTarget.VoiceStub, Output = "" };
        }

        if (t.StartsWith("copilot:", StringComparison.OrdinalIgnoreCase))
        {
            if (!_copilot.IsConfigured)
            {
                _log.Warning("copilot: prefix but Copilot is disabled or missing API key in appsettings.json.");
                return new RoutedCommandResult
                {
                    Target = CommandTarget.AgentExecute,
                    Output =
                        "Copilot API not configured. Enable EriCAShell.Copilot and set Endpoint/ApiKey in appsettings.json.",
                };
            }

            var msg = t["copilot:".Length..].Trim();
            _log.Information("Route: Copilot chat");
            var reply = await _copilot.ChatAsync(msg, cancellationToken);
            return new RoutedCommandResult { Target = CommandTarget.CopilotChat, Output = reply };
        }

        if (streamToAgent)
        {
            _log.Information("Route: agent stream");
            var body = await _agent.ExecuteStreamAsync(t, cancellationToken);
            return new RoutedCommandResult { Target = CommandTarget.AgentStream, Output = body };
        }

        _log.Information("Route: agent execute");
        var raw = await _agent.ExecuteAsync(t, cancellationToken);
        return new RoutedCommandResult { Target = CommandTarget.AgentExecute, Output = raw };
    }
}
