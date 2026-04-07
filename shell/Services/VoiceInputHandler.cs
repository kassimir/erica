using Erica.Shell.Logging;

namespace Erica.Shell.Services;

/// <summary>
/// Push-to-talk / voice capture hook. Wire to Windows.Media.Capture or stream bytes to the agent /voice/stt endpoint.
/// </summary>
public sealed class VoiceInputHandler
{
    private readonly AgentClient _agent;
    private readonly ShellLogger _log;

    public VoiceInputHandler(AgentClient agent, ShellLogger log)
    {
        _agent = agent;
        _log = log;
    }

    public event EventHandler<string>? StatusChanged;

    /// <summary>Placeholder until microphone capture is implemented.</summary>
    public Task<string> TranscribePlaceholderAsync(CancellationToken cancellationToken = default)
    {
        _log.Information("Voice: placeholder transcribe (no audio capture yet).");
        StatusChanged?.Invoke(this, "Voice capture not wired; use agent /voice/stt with raw audio.");
        return Task.FromResult("");
    }

    /// <summary>POST audio bytes to AgentBaseUrl/voice/stt.</summary>
    public async Task<string> TranscribeAudioAsync(byte[] pcmOrWav, CancellationToken cancellationToken = default)
    {
        using var http = new HttpClient();
        var url = $"{_agent.BaseUrl}/voice/stt";
        _log.Information($"POST {url} (audio bytes: {pcmOrWav.Length})");
        using var content = new ByteArrayContent(pcmOrWav);
        var res = await http.PostAsync(url, content, cancellationToken);
        return await res.Content.ReadAsStringAsync(cancellationToken);
    }
}
