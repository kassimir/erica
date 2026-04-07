using System.Diagnostics;

namespace Erica.Shell.Logging;

public enum LogLevel
{
    Trace = 0,
    Debug = 1,
    Information = 2,
    Warning = 3,
    Error = 4
}

public sealed class ShellLogger
{
    private readonly LogLevel _min;

    public ShellLogger(string? minimumLevelName)
    {
        _min = ParseLevel(minimumLevelName ?? "Information");
    }

    private static LogLevel ParseLevel(string name) =>
        Enum.TryParse<LogLevel>(name, true, out var l) ? l : LogLevel.Information;

    public bool IsEnabled(LogLevel level) => level >= _min;

    public void Log(LogLevel level, string message)
    {
        if (!IsEnabled(level))
            return;
        var prefix = $"[{level}] EriCA.Shell";
        Debug.WriteLine($"{prefix} {message}");
    }

    public void Information(string message) => Log(LogLevel.Information, message);
    public void Warning(string message) => Log(LogLevel.Warning, message);
    public void Error(string message) => Log(LogLevel.Error, message);
    public void Error(string message, Exception ex) =>
        Log(LogLevel.Error, $"{message}: {ex.Message}");
}
