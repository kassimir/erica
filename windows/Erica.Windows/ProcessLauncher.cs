using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

namespace Erica.Windows;

/// <summary>Launch processes via shell execute (URLs, .lnk, executables on PATH).</summary>
public static class ProcessLauncher
{
    /// <summary>Start <paramref name="target"/> with default shell handling (same as <c>Start-Process</c>).</summary>
    public static bool TryStart(string target) => TryStart(target, null, null);

    /// <summary>Launch with optional arguments and working directory.</summary>
    public static bool TryStart(string fileName, string? arguments, string? workingDirectory)
    {
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = fileName,
                UseShellExecute = true,
            };
            if (!string.IsNullOrEmpty(arguments))
                psi.Arguments = arguments;
            if (!string.IsNullOrEmpty(workingDirectory))
                psi.WorkingDirectory = workingDirectory;
            Process.Start(psi);
            return true;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>Starts a process and returns it, or <c>null</c> on failure.</summary>
    public static Process? StartProcess(
        string fileName,
        string? arguments = null,
        string? workingDirectory = null,
        bool useShellExecute = true)
    {
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = fileName,
                UseShellExecute = useShellExecute,
            };
            if (!string.IsNullOrEmpty(arguments))
                psi.Arguments = arguments;
            if (!string.IsNullOrEmpty(workingDirectory))
                psi.WorkingDirectory = workingDirectory;
            return Process.Start(psi);
        }
        catch
        {
            return null;
        }
    }

    /// <summary>
    /// Start without shell resolution (no file association / URL handling). Uses kernel32 CreateProcessW.
    /// </summary>
    public static bool TryStartWithCreateProcess(string fileName, string? arguments, string? workingDirectory)
    {
        if (string.IsNullOrWhiteSpace(fileName))
            return false;

        var cmd = new StringBuilder(fileName.Length + (arguments?.Length ?? 0) + 4);
        cmd.Append('"').Append(fileName.Trim()).Append('"');
        if (!string.IsNullOrEmpty(arguments))
        {
            cmd.Append(' ').Append(arguments);
        }

        var si = new NativeMethods.STARTUPINFOW
        {
            cb = Marshal.SizeOf<NativeMethods.STARTUPINFOW>(),
        };

        if (!NativeMethods.CreateProcessW(
                null,
                cmd,
                IntPtr.Zero,
                IntPtr.Zero,
                false,
                0,
                IntPtr.Zero,
                string.IsNullOrEmpty(workingDirectory) ? null : workingDirectory,
                ref si,
                out var pi))
        {
            return false;
        }

        NativeMethods.CloseHandle(pi.hProcess);
        NativeMethods.CloseHandle(pi.hThread);
        return true;
    }
}
