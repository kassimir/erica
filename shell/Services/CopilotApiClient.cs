using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using Erica.Shell.Config;
using Erica.Shell.Logging;

namespace Erica.Shell.Services;

/// <summary>
/// OpenAI-compatible chat completions HTTP client (Azure OpenAI, OpenAI, or org gateways).
/// Point Endpoint/ApiKey at your approved API; Microsoft Copilot surface may differ by tenant.
/// </summary>
public sealed class CopilotApiClient : IDisposable
{
    private readonly HttpClient _http;
    private readonly CopilotSection _cfg;
    private readonly ShellLogger _log;

    public CopilotApiClient(EriCAShellSection settings, ShellLogger log, HttpClient? http = null)
    {
        _cfg = settings.Copilot;
        _log = log;
        _http = http ?? new HttpClient { Timeout = TimeSpan.FromMinutes(2) };
    }

    public bool IsConfigured => _cfg.Enabled
        && !string.IsNullOrWhiteSpace(_cfg.Endpoint)
        && !string.IsNullOrWhiteSpace(_cfg.ApiKey);

    public async Task<string> ChatAsync(string userMessage, CancellationToken cancellationToken = default)
    {
        if (!IsConfigured)
            throw new InvalidOperationException("Copilot API is disabled or missing Endpoint/ApiKey in appsettings.json.");

        var body = new ChatCompletionRequest
        {
            Model = _cfg.Model,
            Messages = new List<ChatMessage>
            {
                new() { Role = "system", Content = _cfg.SystemPrompt },
                new() { Role = "user", Content = userMessage },
            },
        };

        using var req = new HttpRequestMessage(HttpMethod.Post, _cfg.Endpoint)
        {
            Content = JsonContent.Create(body),
        };
        req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", _cfg.ApiKey);

        _log.Information($"POST Copilot-compatible {_cfg.Endpoint}");
        using var res = await _http.SendAsync(req, cancellationToken);
        var json = await res.Content.ReadAsStringAsync(cancellationToken);
        if (!res.IsSuccessStatusCode)
        {
            _log.Error($"Copilot HTTP {(int)res.StatusCode}: {json}");
            return json;
        }

        try
        {
            var parsed = JsonSerializer.Deserialize<ChatCompletionResponse>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true,
            });
            return parsed?.Choices?.FirstOrDefault()?.Message?.Content ?? json;
        }
        catch
        {
            return json;
        }
    }

    public void Dispose() => _http.Dispose();

    private sealed class ChatCompletionRequest
    {
        [JsonPropertyName("model")]
        public string Model { get; init; } = "";

        [JsonPropertyName("messages")]
        public List<ChatMessage> Messages { get; init; } = [];
    }

    private sealed class ChatMessage
    {
        [JsonPropertyName("role")]
        public string Role { get; init; } = "";

        [JsonPropertyName("content")]
        public string Content { get; init; } = "";
    }

    private sealed class ChatCompletionResponse
    {
        [JsonPropertyName("choices")]
        public List<ChoiceDto>? Choices { get; init; }
    }

    private sealed class ChoiceDto
    {
        [JsonPropertyName("message")]
        public MessageDto? Message { get; init; }
    }

    private sealed class MessageDto
    {
        [JsonPropertyName("content")]
        public string? Content { get; init; }
    }
}
