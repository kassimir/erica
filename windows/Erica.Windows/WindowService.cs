using System.Runtime.InteropServices;
using System.Text;
using static Erica.Windows.NativeMethods;

namespace Erica.Windows;

public static class WindowService
{
    public static IReadOnlyList<string> EnumerateVisibleWindowTitles()
    {
        var list = new List<string>();
        EnumWindows((h, _) =>
        {
            if (!IsWindowVisible(h)) return true;
            var sb = new StringBuilder(512);
            GetWindowText(h, sb, sb.Capacity);
            var t = sb.ToString();
            if (!string.IsNullOrWhiteSpace(t))
                list.Add(t);
            return true;
        }, IntPtr.Zero);
        return list;
    }

    public static bool MinimizeForeground()
    {
        var h = GetForegroundWindow();
        if (h == IntPtr.Zero) return false;
        return ShowWindow(h, SW_MINIMIZE);
    }

    public static bool FocusFirstMatchingTitle(string titleSubstring)
    {
        IntPtr found = IntPtr.Zero;
        EnumWindows((h, _) =>
        {
            if (!IsWindowVisible(h)) return true;
            var sb = new StringBuilder(512);
            GetWindowText(h, sb, sb.Capacity);
            var t = sb.ToString();
            if (t.Contains(titleSubstring, StringComparison.OrdinalIgnoreCase))
            {
                found = h;
                return false;
            }
            return true;
        }, IntPtr.Zero);
        if (found == IntPtr.Zero) return false;
        return SetForegroundWindow(found);
    }

    public static bool MoveResize(string titleSubstring, int x, int y, int width, int height)
    {
        IntPtr found = IntPtr.Zero;
        EnumWindows((h, _) =>
        {
            if (!IsWindowVisible(h)) return true;
            var sb = new StringBuilder(512);
            GetWindowText(h, sb, sb.Capacity);
            var t = sb.ToString();
            if (t.Contains(titleSubstring, StringComparison.OrdinalIgnoreCase))
            {
                found = h;
                return false;
            }
            return true;
        }, IntPtr.Zero);
        if (found == IntPtr.Zero) return false;
        return MoveWindow(found, x, y, width, height, true);
    }
}
