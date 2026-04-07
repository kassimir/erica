using System.Diagnostics;
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
                  wifi              { "enable": true|false }  (netsh)
                  audio_volume      { "percent": 0-100 }      (NAudio)
                  audio_device      { "name": "..." }       (list / match)
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
            "launch" => LaunchCmd(root),
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
            "wifi" => WifiCmd(root),
            "audio_volume" => AudioVolumeCmd(root),
            "audio_device" => AudioDeviceCmd(root),
            _ => new { ok = false, error = "unknown command" },
        };

        Console.Out.WriteLine(JsonSerializer.Serialize(result, JsonOpts));
    }

    private static object LaunchCmd(JsonElement root)
    {
        if (!root.TryGetProperty("target", out var t) || string.IsNullOrWhiteSpace(t.GetString()))
            return new { ok = false, error = "missing target" };
        var target = t.GetString()!;
        var useCp = root.TryGetProperty("useCreateProcess", out var ucp) && ucp.GetBoolean();
        if (useCp)
            return new { ok = ProcessLauncher.TryStartWithCreateProcess(target, null, null), method = "CreateProcessW" };
        return new { ok = ProcessLauncher.TryStart(target), method = "ShellExecute" };
    }

    private static object WifiCmd(JsonElement root)
    {
        var enable = root.TryGetProperty("enable", out var e) && e.GetBoolean();
        var arg = enable ? "enable" : "disable";
        var psi = new ProcessStartInfo
        {
            FileName = "netsh",
            Arguments = $"interface set interface \"Wi-Fi\" admin={arg}",
            UseShellExecute = false,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            CreateNoWindow = true,
        };
        using var p = Process.Start(psi);
        if (p == null)
            return new { ok = false, error = "netsh failed to start", enable };
        var err = p.StandardError.ReadToEnd();
        var stdout = p.StandardOutput.ReadToEnd();
        p.WaitForExit(30000);
        var ok = p.ExitCode == 0;
        return new
        {
            ok,
            enable,
            exitCode = p.ExitCode,
            stderr = err.Trim(),
            stdout = stdout.Trim(),
            method = "netsh",
        };
    }

    private static object AudioVolumeCmd(JsonElement root)
    {
        var pct = root.TryGetProperty("percent", out var p) ? p.GetInt32() : 0;
        pct = Math.Clamp(pct, 0, 100);
        var ok = AudioVolumeHelper.TrySetMasterVolumePercent(pct);
        return new { ok, percent = pct, method = "CoreAudio" };
    }

    private static object AudioDeviceCmd(JsonElement root)
    {
        var name = root.TryGetProperty("name", out var n) ? n.GetString() ?? "" : "";
        var devices = AudioVolumeHelper.ListRenderDeviceNames();
        if (string.IsNullOrWhiteSpace(name))
            return new { ok = false, error = "missing name", devices };
        string? matched = null;
        foreach (var d in devices)
        {
            if (d.Contains(name, StringComparison.OrdinalIgnoreCase))
            {
                matched = d;
                break;
            }
        }

        if (matched == null)
            return new { ok = false, error = "no matching device", devices };
        return new
        {
            ok = true,
            matched,
            devices,
            message = "Default device switch: use Python audio_skill optional pycaw path if CLI cannot set policy.",
        };
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
