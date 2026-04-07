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

    public static EriCAShellSection Load(string? baseDirectory = null)
    {
        baseDirectory ??= AppContext.BaseDirectory;
        var path = Path.Combine(baseDirectory, "appsettings.json");
        if (!File.Exists(path))
        {
            var log = new ShellLogger("Information");
            log.Warning($"appsettings.json not found at {path}; using defaults.");
            return new EriCAShellSection();
        }

        var json = File.ReadAllText(path);
        var root = JsonSerializer.Deserialize<ShellSettingsRoot>(json, JsonOptions);
        return root?.EriCAShell ?? new EriCAShellSection();
    }
}
