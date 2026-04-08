using System.Text.Json;
using System.Text.Json.Serialization;

namespace Erica.Shell.Services;

/// <summary>Matches FastAPI /plan and /execute <c>Plan</c> JSON (snake_case fields).</summary>
public sealed class PlanResponseDto
{
    [JsonPropertyName("plan")]
    public PlanDto? Plan { get; set; }

    [JsonPropertyName("message")]
    public string Message { get; set; } = "";
}

public sealed class PlanDto
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = "";

    [JsonPropertyName("steps")]
    public List<PlanStepDto> Steps { get; set; } = new();

    [JsonPropertyName("rationale")]
    public string Rationale { get; set; } = "";
}

public sealed class PlanStepDto
{
    [JsonPropertyName("skill_id")]
    public string SkillId { get; set; } = "";

    [JsonPropertyName("arguments")]
    public Dictionary<string, JsonElement>? Arguments { get; set; }
}
