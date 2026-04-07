using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using static Erica.Windows.NativeMethods;

namespace Erica.Windows;

/// <summary>
/// High-level window operations: enumeration, titles, focus, minimize / maximize / restore, placement, move/resize.
/// </summary>
public static class WindowService
{
    /// <summary>Enumerate visible top-level windows with title, class name, and screen bounds.</summary>
    public static IReadOnlyList<WindowDescriptor> ListVisibleWindows(bool includeEmptyTitle = false)
    {
        var list = new List<WindowDescriptor>();
        EnumWindows(
            (h, _) =>
            {
                if (!IsWindow(h) || !IsWindowVisible(h))
                    return true;

                var title = GetWindowTitle(h);
                if (!includeEmptyTitle && string.IsNullOrWhiteSpace(title))
                    return true;

                if (!GetWindowRect(h, out var rect))
                    return true;

                var cls = GetWindowClassName(h);
                list.Add(WindowDescriptor.Create(h, rect, title, cls));
                return true;
            },
            IntPtr.Zero);
        return list;
    }

    /// <summary>Legacy: title strings only.</summary>
    public static IReadOnlyList<string> EnumerateVisibleWindowTitles()
    {
        return ListVisibleWindows(includeEmptyTitle: false).Select(w => w.Title).Where(t => !string.IsNullOrWhiteSpace(t)).ToList();
    }

    public static string GetWindowTitle(IntPtr hWnd)
    {
        var sb = new StringBuilder(512);
        _ = GetWindowText(hWnd, sb, sb.Capacity);
        return sb.ToString();
    }

    public static string GetWindowClassName(IntPtr hWnd)
    {
        var sb = new StringBuilder(256);
        _ = GetClassNameW(hWnd, sb, sb.Capacity);
        return sb.ToString();
    }

    public static bool TryGetWindowRect(IntPtr hWnd, out WindowRect rect)
    {
        rect = default;
        if (!GetWindowRect(hWnd, out var r))
            return false;
        rect = WindowRect.FromRect(in r);
        return true;
    }

    /// <summary>Find first visible top-level window whose title contains <paramref name="titleSubstring"/>.</summary>
    public static IntPtr FindVisibleWindowByTitleSubstring(string titleSubstring)
    {
        if (string.IsNullOrEmpty(titleSubstring))
            return IntPtr.Zero;
        IntPtr found = IntPtr.Zero;
        EnumWindows(
            (h, _) =>
            {
                if (!IsWindowVisible(h))
                    return true;
                var t = GetWindowTitle(h);
                if (t.Contains(titleSubstring, StringComparison.OrdinalIgnoreCase))
                {
                    found = h;
                    return false;
                }
                return true;
            },
            IntPtr.Zero);
        return found;
    }

    public static string? GetForegroundWindowTitle()
    {
        var h = GetForegroundWindow();
        if (h == IntPtr.Zero)
            return null;
        var t = GetWindowTitle(h);
        return string.IsNullOrEmpty(t) ? null : t;
    }

    /// <summary>Best-effort foreground (uses AttachThreadInput when needed).</summary>
    public static bool TrySetForegroundWindow(IntPtr hWnd)
    {
        if (hWnd == IntPtr.Zero || !IsWindow(hWnd))
            return false;

        AllowSetForegroundWindow(ASFW_ANY);

        var fg = GetForegroundWindow();
        if (fg == hWnd)
            return true;

        var fgThread = GetWindowThreadProcessId(fg, out _);
        var curThread = GetCurrentThreadId();
        if (fgThread == curThread)
            return SetForegroundWindow(hWnd);

        _ = AttachThreadInput(curThread, fgThread, true);
        var ok = SetForegroundWindow(hWnd);
        _ = AttachThreadInput(curThread, fgThread, false);
        return ok;
    }

    public static bool FocusFirstMatchingTitle(string titleSubstring)
    {
        var hwnd = FindVisibleWindowByTitleSubstring(titleSubstring);
        if (hwnd == IntPtr.Zero)
            return false;
        return TrySetForegroundWindow(hwnd);
    }

    public static bool MinimizeForeground()
    {
        var h = GetForegroundWindow();
        if (h == IntPtr.Zero)
            return false;
        return ShowWindow(h, SW_MINIMIZE);
    }

    public static bool MinimizeWindow(IntPtr hWnd)
    {
        if (hWnd == IntPtr.Zero)
            return false;
        return ShowWindow(hWnd, SW_MINIMIZE);
    }

    public static bool MaximizeWindow(IntPtr hWnd)
    {
        if (hWnd == IntPtr.Zero)
            return false;
        return ShowWindow(hWnd, SW_MAXIMIZE);
    }

    public static bool MaximizeForeground()
    {
        var h = GetForegroundWindow();
        return h != IntPtr.Zero && ShowWindow(h, SW_MAXIMIZE);
    }

    public static bool RestoreWindow(IntPtr hWnd)
    {
        if (hWnd == IntPtr.Zero)
            return false;
        return ShowWindow(hWnd, SW_RESTORE);
    }

    public static bool RestoreForeground()
    {
        var h = GetForegroundWindow();
        return h != IntPtr.Zero && ShowWindow(h, SW_RESTORE);
    }

    public static bool MoveResize(string titleSubstring, int x, int y, int width, int height)
    {
        var found = FindVisibleWindowByTitleSubstring(titleSubstring);
        if (found == IntPtr.Zero)
            return false;
        return MoveWindow(found, x, y, width, height, true);
    }

    public static bool MoveResizeWindow(IntPtr hWnd, int x, int y, int width, int height)
    {
        if (hWnd == IntPtr.Zero)
            return false;
        return MoveWindow(hWnd, x, y, width, height, true);
    }

    /// <summary>Read placement (show command + normal restored bounds).</summary>
    public static bool TryGetWindowPlacementInfo(IntPtr hWnd, out WindowPlacementInfo info)
    {
        info = default;
        if (hWnd == IntPtr.Zero)
            return false;
        var wp = new WINDOWPLACEMENT { length = (uint)Marshal.SizeOf<WINDOWPLACEMENT>() };
        if (!GetWindowPlacement(hWnd, ref wp))
            return false;
        info = new WindowPlacementInfo
        {
            ShowCmd = wp.showCmd,
            NormalBounds = WindowRect.FromRect(in wp.rcNormalPosition),
        };
        return true;
    }

    public static bool IsWindowMinimized(IntPtr hWnd) => hWnd != IntPtr.Zero && IsIconic(hWnd);

    public static bool IsWindowMaximized(IntPtr hWnd) => hWnd != IntPtr.Zero && IsZoomed(hWnd);
}
