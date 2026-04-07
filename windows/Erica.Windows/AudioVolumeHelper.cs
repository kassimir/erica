using System.Collections.Generic;
using NAudio.CoreAudioApi;

namespace Erica.Windows;

/// <summary>Default render endpoint volume and device listing via Core Audio (NAudio).</summary>
public static class AudioVolumeHelper
{
    public static bool TrySetMasterVolumePercent(int percent)
    {
        if (percent is < 0 or > 100)
            return false;
        try
        {
            using var enumerator = new MMDeviceEnumerator();
            using var device = enumerator.GetDefaultAudioEndpoint(DataFlow.Render, Role.Multimedia);
            device.AudioEndpointVolume.MasterVolumeLevelScalar = percent / 100f;
            return true;
        }
        catch
        {
            return false;
        }
    }

    public static IReadOnlyList<string> ListRenderDeviceNames()
    {
        var list = new List<string>();
        try
        {
            using var enumerator = new MMDeviceEnumerator();
            foreach (var d in enumerator.EnumerateAudioEndPoints(DataFlow.Render, DeviceState.Active))
                list.Add(d.FriendlyName);
        }
        catch
        {
            // ignore
        }

        return list;
    }
}
