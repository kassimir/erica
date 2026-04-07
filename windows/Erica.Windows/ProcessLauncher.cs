using System.Diagnostics;

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
}
