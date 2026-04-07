using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Erica.Shell.Config;
using Erica.Shell.Logging;

namespace Erica.Shell.Services;

public sealed class AgentClient
{
    private readonly HttpClient _http;
    private readonly EriCAShellSection _settings;
    private readonly ShellLogger _log;

    public AgentClient(EriCAShellSection settings, ShellLogger log, HttpClient? http = null)
    {
        _settings = settings;
        _log = log;
        _http = http ?? new HttpClient { Timeout = TimeSpan.FromMinutes(5) };
    }

    public string BaseUrl => _settings.AgentBaseUrl.TrimEnd('/');

    public async Task<string> ExecuteAsync(string text, CancellationToken cancellationToken = default)
    {
        var url = $"{BaseUrl}/execute";
        _log.Information($"POST {url}");
        var res = await _http.PostAsJsonAsync(url, new { text }, cancellationToken);
        return await res.Content.ReadAsStringAsync(cancellationToken);
    }

    public async Task<string> ExecuteStreamAsync(string text, CancellationToken cancellationToken = default)
    {
        var url = $"{BaseUrl}/execute/stream";
        _log.Information($"POST {url} (stream)");
        using var req = new HttpRequestMessage(HttpMethod.Post, url)
        {
            Content = JsonContent.Create(new { text }),
        };
        using var res = await _http.SendAsync(req, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
        await using var stream = await res.Content.ReadAsStreamAsync(cancellationToken);
        using var reader = new StreamReader(stream);
        var sb = new StringBuilder();
        while (!reader.EndOfStream)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var line = await reader.ReadLineAsync(cancellationToken);
            if (string.IsNullOrWhiteSpace(line))
                continue;
            try
            {
                var chunk = JsonSerializer.Deserialize<StreamChunkDto>(
                    line,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
                if (chunk?.Text is { Length: > 0 })
                    sb.AppendLine(chunk.Text);
            }
            catch
            {
                sb.AppendLine(line);
            }
        }
        return sb.ToString();
    }

    private sealed class StreamChunkDto
    {
        public string? Text { get; set; }
        public bool Done { get; set; }
    }
}
