using System.Net.Http.Json;
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
                       ?? new List<Benefit>();

        return benefits
            .OrderBy(b => b.Name, StringComparer.OrdinalIgnoreCase)
            .ToList();
    }
}

