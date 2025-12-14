namespace SoldierSave.Web.Models;

public class Benefit
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Url { get; set; } = string.Empty;
    public List<string> Urls { get; set; } = new();
    public string Summary { get; set; } = string.Empty;
    public List<string> Categories { get; set; } = new();
    public List<string> Tags { get; set; } = new();
    public List<string> Eligibility { get; set; } = new();
    public BenefitSource? Source { get; set; }
    public string AddedBy { get; set; } = string.Empty;
    public DateTimeOffset? AddedAt { get; set; }
}

public class BenefitSource
{
    public string? Type { get; set; }
    public string? Reference { get; set; }
}
