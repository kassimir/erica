using System.Diagnostics;

namespace Erica.Windows;

public static class ProcessLauncher
{
    public static bool TryStart(string target)
    {
        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = target,
                UseShellExecute = true,
            });
            return true;
        }
        catch
        {
            return false;
        }
    }
}
