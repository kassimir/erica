using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Erica.Shell.Config;
using Erica.Shell.Logging;

namespace Erica.Shell.Services;

public sealed class AgentClient
{
    private const int MaxAttempts = 3;
    private static readonly TimeSpan[] Backoffs = [TimeSpan.Zero, TimeSpan.FromMilliseconds(400), TimeSpan.FromMilliseconds(900)];

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

    /// <summary>GET /health — agent reachability and active persona mode.</summary>
    public async Task<AgentHealthResult?> GetHealthAsync(CancellationToken cancellationToken = default)
    {
        for (var attempt = 0; attempt < MaxAttempts; attempt++)
        {
            try
            {
                if (attempt > 0)
                    await Task.Delay(Backoffs[attempt], cancellationToken).ConfigureAwait(false);

                var url = $"{BaseUrl}/health";
                var res = await _http.GetAsync(url, cancellationToken).ConfigureAwait(false);
                var json = await res.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
                if (!res.IsSuccessStatusCode)
                    return new AgentHealthResult { Ok = false, Mode = null };
                return JsonSerializer.Deserialize<AgentHealthResult>(
                    json,
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            }
            catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
            {
                throw;
            }
            catch (Exception ex) when (IsTransient(ex) && attempt < MaxAttempts - 1)
            {
                _log.Warning($"Health check retry ({attempt + 1}/{MaxAttempts}): {ex.Message}");
            }
            catch (Exception ex)
            {
                _log.Warning($"Health check failed: {ex.Message}");
                return null;
            }
        }

        return null;
    }

    public async Task<string> ExecuteAsync(string text, CancellationToken cancellationToken = default)
    {
        var url = $"{BaseUrl}/execute";
        _log.Information($"POST {url}");
        return await WithRetryAsync(
            async () =>
            {
                var res = await _http.PostAsJsonAsync(url, new { text }, cancellationToken).ConfigureAwait(false);
                res.EnsureSuccessStatusCode();
                return await res.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            },
            cancellationToken).ConfigureAwait(false);
    }

    /// <summary>Buffered stream (legacy).</summary>
    public async Task<string> ExecuteStreamAsync(string text, CancellationToken cancellationToken = default)
    {
        var sb = new StringBuilder();
        await ExecuteStreamAsync(
            text,
            new Progress<string>(line => sb.AppendLine(line)),
            cancellationToken).ConfigureAwait(false);
        return sb.ToString();
    }

    /// <summary>NDJSON lines from <c>/execute/stream</c>; each decoded text chunk reported to <paramref name="onChunk"/>.</summary>
    public async Task ExecuteStreamAsync(
        string text,
        IProgress<string> onChunk,
        CancellationToken cancellationToken = default)
    {
        var url = $"{BaseUrl}/execute/stream";
        _log.Information($"POST {url} (stream, incremental)");

        await WithRetryAsync(
            async () =>
            {
                using var req = new HttpRequestMessage(HttpMethod.Post, url)
                {
                    Content = JsonContent.Create(new { text }),
                };
                using var res = await _http.SendAsync(req, HttpCompletionOption.ResponseHeadersRead, cancellationToken)
                    .ConfigureAwait(false);
                res.EnsureSuccessStatusCode();
                await using var stream = await res.Content.ReadAsStreamAsync(cancellationToken).ConfigureAwait(false);
                using var reader = new StreamReader(stream);
                while (!reader.EndOfStream)
                {
                    cancellationToken.ThrowIfCancellationRequested();
                    var line = await reader.ReadLineAsync(cancellationToken).ConfigureAwait(false);
                    if (string.IsNullOrWhiteSpace(line))
                        continue;
                    try
                    {
                        var chunk = JsonSerializer.Deserialize<StreamChunkDto>(
                            line,
                            new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
                        if (chunk?.Text is { Length: > 0 })
                            onChunk.Report(chunk.Text);
                        else if (!string.IsNullOrWhiteSpace(line))
                            onChunk.Report(line);
                    }
                    catch
                    {
                        onChunk.Report(line);
                    }
                }
            },
            cancellationToken).ConfigureAwait(false);
    }

    private async Task<T> WithRetryAsync<T>(Func<Task<T>> action, CancellationToken cancellationToken)
    {
        for (var attempt = 0; attempt < MaxAttempts; attempt++)
        {
            try
            {
                if (attempt > 0)
                    await Task.Delay(Backoffs[attempt], cancellationToken).ConfigureAwait(false);
                return await action().ConfigureAwait(false);
            }
            catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
            {
                throw;
            }
            catch (Exception ex) when (IsTransient(ex) && attempt < MaxAttempts - 1)
            {
                _log.Warning($"Transient HTTP error (attempt {attempt + 1}/{MaxAttempts}): {ex.Message}");
                continue;
            }
            catch
            {
                throw;
            }
        }

        throw new HttpRequestException("Request failed after retries.");
    }

    private async Task WithRetryAsync(Func<Task> action, CancellationToken cancellationToken)
    {
        for (var attempt = 0; attempt < MaxAttempts; attempt++)
        {
            try
            {
                if (attempt > 0)
                    await Task.Delay(Backoffs[attempt], cancellationToken).ConfigureAwait(false);
                await action().ConfigureAwait(false);
                return;
            }
            catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
            {
                throw;
            }
            catch (Exception ex) when (IsTransient(ex) && attempt < MaxAttempts - 1)
            {
                _log.Warning($"Transient HTTP error (attempt {attempt + 1}/{MaxAttempts}): {ex.Message}");
                continue;
            }
            catch
            {
                throw;
            }
        }

        throw new HttpRequestException("Request failed after retries.");
    }

    private static bool IsTransient(Exception ex)
    {
        return ex is HttpRequestException or IOException
            or TaskCanceledException;
    }

    private sealed class StreamChunkDto
    {
        public string? Text { get; set; }
        public bool Done { get; set; }
    }
}

public sealed class AgentHealthResult
{
    public bool Ok { get; set; }
    public string? Mode { get; set; }
}
