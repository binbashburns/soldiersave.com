using System.Net.Http.Json;
using System.Text.Json;
using SoldierSave.Web.Models;

namespace SoldierSave.Web.Services;

public class BenefitService
{
    private readonly HttpClient _httpClient;

    public BenefitService(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<IReadOnlyList<Benefit>> GetBenefitsAsync(CancellationToken cancellationToken = default)
    {
        var benefits = await _httpClient.GetFromJsonAsync<List<Benefit>>("data/benefits.json", cancellationToken)
                       ?? throw new JsonException("The benefits catalog must be an array.");

        if (benefits.Any(b => b is null || b.Name is null || b.Summary is null ||
                              b.Tags is null || b.Categories is null ||
                              b.Tags.Any(t => t is null) || b.Categories.Any(c => c is null)))
        {
            throw new JsonException("The benefits catalog contains invalid entries.");
        }

        return benefits
            .OrderBy(b => b.Name, StringComparer.OrdinalIgnoreCase)
            .ToList();
    }
}
