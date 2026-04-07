using System.Text.Json;
using Erica.Shell.Logging;

namespace Erica.Shell.Config;

public static class ShellConfiguration
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
    };

    public static EriCAShellSection Load(string? baseDirectory = null, ShellStartupOptions? startup = null)
    {
        baseDirectory ??= AppContext.BaseDirectory;
        var path = Path.Combine(baseDirectory, "appsettings.json");
        EriCAShellSection section;
        if (!File.Exists(path))
        {
            var log = new ShellLogger("Information");
            log.Warning($"appsettings.json not found at {path}; using defaults.");
            section = new EriCAShellSection();
        }
        else
        {
            var json = File.ReadAllText(path);
            var root = JsonSerializer.Deserialize<ShellSettingsRoot>(json, JsonOptions);
            section = root?.EriCAShell ?? new EriCAShellSection();
        }

        return ApplyAgentUrlOverrides(section, startup);
    }

    /// <summary>Resolution order: <c>--agent-url</c>, then <c>ERICA_AGENT_URL</c>, then JSON default.</summary>
    public static EriCAShellSection ApplyAgentUrlOverrides(EriCAShellSection section, ShellStartupOptions? startup)
    {
        string? url = null;
        if (!string.IsNullOrWhiteSpace(startup?.AgentUrlOverride))
            url = startup.AgentUrlOverride.Trim();
        else if (!string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable("ERICA_AGENT_URL")))
            url = Environment.GetEnvironmentVariable("ERICA_AGENT_URL")!.Trim();

        if (string.IsNullOrWhiteSpace(url))
            return section;

        url = url.TrimEnd('/');
        return new EriCAShellSection
        {
            AgentBaseUrl = url,
            WindowMode = section.WindowMode,
            Copilot = section.Copilot,
            Logging = section.Logging,
        };
    }
}
