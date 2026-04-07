using Erica.Shell.Config;
using Erica.Shell.Logging;
using Erica.Shell.Services;

namespace Erica.Shell;

/// <summary>
/// Composition root for the WinUI shell: configuration, logging, and shared services.
/// </summary>
public static class ShellAppHost
{
    private static bool _initialized;
    private static EriCAShellSection? _settings;
    private static ShellLogger? _log;
    private static AgentClient? _agent;
    private static CopilotApiClient? _copilot;
    private static VoiceInputHandler? _voice;
    private static CommandRouter? _router;

    public static ShellLogger Log => _log ?? throw new InvalidOperationException("ShellAppHost not initialized.");
    public static AgentClient Agent => _agent ?? throw new InvalidOperationException("ShellAppHost not initialized.");
    public static CommandRouter Router => _router ?? throw new InvalidOperationException("ShellAppHost not initialized.");
    public static VoiceInputHandler Voice => _voice ?? throw new InvalidOperationException("ShellAppHost not initialized.");
    public static EriCAShellSection Settings => _settings ?? throw new InvalidOperationException("ShellAppHost not initialized.");

    public static void Initialize(ShellStartupOptions? startup = null)
    {
        if (_initialized)
            return;

        _settings = ShellConfiguration.Load(startup: startup);
        _log = new ShellLogger(_settings.Logging.MinimumLevel);
        _log.Information($"EriCA Shell starting. Agent: {_settings.AgentBaseUrl}");

        _agent = new AgentClient(_settings, _log);
        _copilot = new CopilotApiClient(_settings, _log);
        _voice = new VoiceInputHandler(_agent, _log);
        _router = new CommandRouter(_agent, _copilot, _voice, _log);

        _initialized = true;
    }
}
