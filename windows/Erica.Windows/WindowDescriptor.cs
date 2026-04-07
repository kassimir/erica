namespace Erica.Windows;

/// <summary>Visible top-level window summary for enumeration and JSON export.</summary>
public sealed class WindowDescriptor
{
    /// <summary>Window handle as integer (JSON-friendly).</summary>
    public long Handle { get; init; }

    public string Title { get; init; } = "";
    public WindowRect Bounds { get; init; }
    public string ClassName { get; init; } = "";

    internal static WindowDescriptor Create(IntPtr hwnd, NativeMethods.RECT rect, string title, string className) =>
        new()
        {
            Handle = hwnd.ToInt64(),
            Title = title,
            Bounds = WindowRect.FromRect(in rect),
            ClassName = className,
        };
}
