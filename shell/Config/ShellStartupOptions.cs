namespace Erica.Shell.Config;

/// <summary>Command-line and startup overrides (merged after appsettings.json).</summary>
public sealed class ShellStartupOptions
{
    /// <summary>Optional override from <c>--agent-url</c>.</summary>
    public string? AgentUrlOverride { get; init; }

    /// <summary>Parse <c>--agent-url &lt;url&gt;</c> from process arguments (index 0 is the executable).</summary>
    public static ShellStartupOptions Parse(string[]? commandLineArgs)
    {
        if (commandLineArgs is not { Length: > 1 })
            return new ShellStartupOptions();

        for (var i = 1; i < commandLineArgs.Length - 1; i++)
        {
            if (string.Equals(commandLineArgs[i], "--agent-url", StringComparison.OrdinalIgnoreCase))
            {
                var url = commandLineArgs[i + 1]?.Trim();
                if (!string.IsNullOrEmpty(url))
                    return new ShellStartupOptions { AgentUrlOverride = url };
            }
        }

        return new ShellStartupOptions();
    }
}
