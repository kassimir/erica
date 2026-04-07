namespace Erica.Windows;

/// <summary>Axis-aligned window bounds in screen coordinates (Win32 RECT).</summary>
public readonly struct WindowRect
{
    public int Left { get; init; }
    public int Top { get; init; }
    public int Right { get; init; }
    public int Bottom { get; init; }

    public int Width => Right - Left;
    public int Height => Bottom - Top;

    internal static WindowRect FromRect(in NativeMethods.RECT r) =>
        new()
        {
            Left = r.Left,
            Top = r.Top,
            Right = r.Right,
            Bottom = r.Bottom,
        };
}
