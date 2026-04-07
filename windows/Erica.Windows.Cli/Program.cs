using System.Text.Json;
using Erica.Windows;

namespace Erica.Windows.Cli;

internal static class Program
{
    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = false,
    };

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
                """
                Usage: Erica.Windows.Cli <command> [stdin JSON]

                Commands:
                  launch            { "target": "notepad" }
                  window_minimize   { } foreground | { "title": "substring" }
                  window_maximize   { "foreground": true } | { "title": "substring" }
                  window_restore    { "foreground": true } | { "title": "substring" }
                  window_move       { "title", "x", "y", "width", "height" }
                  foreground_title  { }
                  list_windows      { }   (titles only)
                  window_list       { }   (handles, titles, bounds, class names)
                  window_placement  { "handle": 12345 }
                  wifi              { "enable": true|false }  (stub)
                  audio_volume      { "percent": 0-100 }      (stub)
                  audio_device      { "name": "..." }       (stub)
                """);
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
            "window_minimize" => MinimizeCmd(root),
            "window_maximize" => MaximizeCmd(root),
            "window_restore" => RestoreCmd(root),
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
            "foreground_title" => new { ok = true, title = WindowService.GetForegroundWindowTitle() },
            "list_windows" => new { ok = true, titles = WindowService.EnumerateVisibleWindowTitles() },
            "window_list" => new { ok = true, windows = WindowService.ListVisibleWindows() },
            "window_placement" => PlacementCmd(root),
            "wifi" => new
            {
                ok = true,
                message = "Stub: use netsh or native WLAN API from a dedicated skill.",
                enable = root.TryGetProperty("enable", out var e) && e.GetBoolean(),
            },
            "audio_volume" => new
            {
                ok = true,
                message = "Stub: wire Core Audio (endpoint volume) for production.",
                percent = root.TryGetProperty("percent", out var p) ? p.GetInt32() : 0,
            },
            "audio_device" => new
            {
                ok = false,
                message = "Requires Core Audio policy / device enumeration.",
                name = root.TryGetProperty("name", out var n) ? n.GetString() : "",
            },
            _ => new { ok = false, error = "unknown command" },
        };

        Console.Out.WriteLine(JsonSerializer.Serialize(result, JsonOpts));
    }

    private static object MinimizeCmd(JsonElement root)
    {
        if (root.TryGetProperty("foreground", out var fg) && fg.GetBoolean())
            return new { ok = WindowService.MinimizeForeground() };
        if (root.TryGetProperty("title", out var t))
        {
            var hwnd = WindowService.FindVisibleWindowByTitleSubstring(t.GetString() ?? "");
            return new { ok = hwnd != IntPtr.Zero && WindowService.MinimizeWindow(hwnd) };
        }
        return new { ok = WindowService.MinimizeForeground() };
    }

    private static object MaximizeCmd(JsonElement root)
    {
        if (root.TryGetProperty("foreground", out var fg) && fg.GetBoolean())
            return new { ok = WindowService.MaximizeForeground() };
        if (root.TryGetProperty("title", out var t))
        {
            var hwnd = WindowService.FindVisibleWindowByTitleSubstring(t.GetString() ?? "");
            return new { ok = hwnd != IntPtr.Zero && WindowService.MaximizeWindow(hwnd) };
        }
        return new { ok = false, error = "use foreground:true or title" };
    }

    private static object RestoreCmd(JsonElement root)
    {
        if (root.TryGetProperty("foreground", out var fg) && fg.GetBoolean())
            return new { ok = WindowService.RestoreForeground() };
        if (root.TryGetProperty("title", out var t))
        {
            var hwnd = WindowService.FindVisibleWindowByTitleSubstring(t.GetString() ?? "");
            return new { ok = hwnd != IntPtr.Zero && WindowService.RestoreWindow(hwnd) };
        }
        return new { ok = false, error = "use foreground:true or title" };
    }

    private static object PlacementCmd(JsonElement root)
    {
        if (!root.TryGetProperty("handle", out var hEl))
            return new { ok = false, error = "missing handle" };
        var ptr = new IntPtr(hEl.GetInt64());
        if (!WindowService.TryGetWindowPlacementInfo(ptr, out var info))
            return new { ok = false, error = "GetWindowPlacement failed" };
        return new
        {
            ok = true,
            showCmd = info.ShowCmd,
            normalLeft = info.NormalBounds.Left,
            normalTop = info.NormalBounds.Top,
            normalRight = info.NormalBounds.Right,
            normalBottom = info.NormalBounds.Bottom,
        };
    }
}
