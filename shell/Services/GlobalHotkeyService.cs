using System.Runtime.InteropServices;
using Microsoft.UI.Dispatching;

namespace Erica.Shell.Services;

/// <summary>System-wide hotkeys via RegisterHotKey + WM_HOTKEY (window subclass).</summary>
public sealed class GlobalHotkeyService : IDisposable
{
    public const int IdPalette = 9001;
    public const int IdQuake = 9002;
    public const int IdVoice = 9003;

    private const uint ModControl = 0x0002;
    private const uint ModShift = 0x0004;
    private const uint ModNorepeat = 0x4000;

    private const uint VkSpace = 0x20;
    private const uint VkOem3 = 0xc0; // US backtick `~
    private const uint VkV = 0x56;

    private const uint WmHotkey = 0x0312;

    private readonly IntPtr _hwnd;
    private readonly GCHandle _gc;
    private bool _disposed;

    private sealed class HotkeyContext
    {
        public required DispatcherQueue Dq { get; init; }
        public required Action<int> OnHotkey { get; init; }
    }

    private static readonly SUBCLASSPROC SubclassProcStatic = SubclassProc;

    public GlobalHotkeyService(IntPtr hwnd, DispatcherQueue dq, Action<int> onHotkey)
    {
        _hwnd = hwnd;
        var ctx = new HotkeyContext { Dq = dq, OnHotkey = onHotkey };
        _gc = GCHandle.Alloc(ctx);

        if (!SetWindowSubclass(
                hwnd,
                SubclassProcStatic,
                new UIntPtr(1),
                (UIntPtr)(ulong)GCHandle.ToIntPtr(_gc)))
        {
            _gc.Free();
            throw new InvalidOperationException("SetWindowSubclass failed.");
        }

        if (!TryRegisterAll())
        {
            RemoveWindowSubclass(hwnd, SubclassProcStatic, new UIntPtr(1));
            _gc.Free();
            throw new InvalidOperationException("RegisterHotKey failed (another app may own a combo).");
        }
    }

    private bool TryRegisterAll()
    {
        // Ctrl+Space — palette
        if (!RegisterHotKey(_hwnd, IdPalette, ModControl | ModNorepeat, VkSpace))
            return false;
        // Ctrl+` — Quake
        if (!RegisterHotKey(_hwnd, IdQuake, ModControl | ModNorepeat, VkOem3))
        {
            UnregisterHotKey(_hwnd, IdPalette);
            return false;
        }

        // Ctrl+Shift+V — voice
        if (!RegisterHotKey(_hwnd, IdVoice, ModControl | ModShift | ModNorepeat, VkV))
        {
            UnregisterHotKey(_hwnd, IdPalette);
            UnregisterHotKey(_hwnd, IdQuake);
            return false;
        }

        return true;
    }

    private static IntPtr SubclassProc(
        IntPtr hwnd,
        uint msg,
        IntPtr wParam,
        IntPtr lParam,
        UIntPtr uIdSubclass,
        UIntPtr dwRefData)
    {
        if (msg == WmHotkey && dwRefData != UIntPtr.Zero)
        {
            var gch = GCHandle.FromIntPtr((nint)(ulong)dwRefData);
            if (gch.Target is HotkeyContext ctx)
            {
                var id = wParam.ToInt32();
                ctx.Dq.TryEnqueue(() => ctx.OnHotkey(id));
            }

            return IntPtr.Zero;
        }

        return DefSubclassProc(hwnd, msg, wParam, lParam);
    }

    public void Dispose()
    {
        if (_disposed)
            return;
        _disposed = true;

        UnregisterHotKey(_hwnd, IdPalette);
        UnregisterHotKey(_hwnd, IdQuake);
        UnregisterHotKey(_hwnd, IdVoice);
        RemoveWindowSubclass(_hwnd, SubclassProcStatic, new UIntPtr(1));
        if (_gc.IsAllocated)
            _gc.Free();
    }

    [UnmanagedFunctionPointer(CallingConvention.Winapi)]
    private delegate IntPtr SUBCLASSPROC(
        IntPtr hWnd,
        uint uMsg,
        IntPtr wParam,
        IntPtr lParam,
        UIntPtr uIdSubclass,
        UIntPtr dwRefData);

    [DllImport("comctl32.dll")]
    private static extern bool SetWindowSubclass(
        IntPtr hWnd,
        SUBCLASSPROC pfnSubclass,
        UIntPtr uIdSubclass,
        UIntPtr dwRefData);

    [DllImport("comctl32.dll")]
    private static extern bool RemoveWindowSubclass(IntPtr hWnd, SUBCLASSPROC pfnSubclass, UIntPtr uIdSubclass);

    [DllImport("comctl32.dll")]
    private static extern IntPtr DefSubclassProc(IntPtr hWnd, uint uMsg, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool UnregisterHotKey(IntPtr hWnd, int id);
}
