using System.Text.Json;
using Erica.Windows;

namespace Erica.Windows.Cli;

internal static class Program
{
    private static string ReadStdin()
    {
        using var sr = new StreamReader(Console.OpenStandardInput());
        return sr.ReadToEnd();
    }

    private static void Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine(
                "Usage: Erica.Windows.Cli <launch|window_minimize|window_move|wifi|audio_volume|audio_device|list_windows>");
            Environment.Exit(1);
            return;
        }

        var cmd = args[0].ToLowerInvariant();
        var json = ReadStdin();
        using var doc = JsonDocument.Parse(string.IsNullOrWhiteSpace(json) ? "{}" : json);
        var root = doc.RootElement;

        object result = cmd switch
        {
            "launch" => new
            {
                ok = root.TryGetProperty("target", out var t) && ProcessLauncher.TryStart(t.GetString() ?? ""),
            },
            "window_minimize" => new { ok = WindowService.MinimizeForeground() },
            "window_move" => new
            {
                ok = root.TryGetProperty("title", out var title)
                    && root.TryGetProperty("x", out var x)
                    && root.TryGetProperty("y", out var y)
                    && root.TryGetProperty("width", out var w)
                    && root.TryGetProperty("height", out var h)
                    && WindowService.MoveResize(
                        title.GetString() ?? "",
                        x.GetInt32(),
                        y.GetInt32(),
                        w.GetInt32(),
                        h.GetInt32()),
            },
            "wifi" => new
            {
                ok = true,
                message = "Stub: integrate netsh or WLAN API as needed.",
                enable = root.TryGetProperty("enable", out var e) && e.GetBoolean(),
            },
            "audio_volume" => new
            {
                ok = true,
                message = "Stub: wire Core Audio APIs for production.",
                percent = root.TryGetProperty("percent", out var p) ? p.GetInt32() : 0,
            },
            "audio_device" => new
            {
                ok = false,
                message = "Requires Core Audio policy config in production.",
                name = root.TryGetProperty("name", out var n) ? n.GetString() : "",
            },
            "list_windows" => new { ok = true, titles = WindowService.EnumerateVisibleWindowTitles() },
            _ => new { ok = false, error = "unknown command" },
        };

        Console.Out.WriteLine(JsonSerializer.Serialize(result));
    }
}
