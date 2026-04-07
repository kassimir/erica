namespace Erica.Windows;

/// <summary>Subset of Win32 <c>WINDOWPLACEMENT</c> for public API.</summary>
public readonly struct WindowPlacementInfo
{
    /// <summary>Show command (e.g. SW_NORMAL, SW_MAXIMIZE).</summary>
    public uint ShowCmd { get; init; }

    /// <summary>Restored size in workspace coordinates.</summary>
    public WindowRect NormalBounds { get; init; }
}
