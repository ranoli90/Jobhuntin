
$competitors = @(
    "Resume Worded",
    "Rezi",
    "Kickresume",
    "Enhancv",
    "Zety",
    "Novoresume",
    "Hiration",
    "Jobsolv",
    "Wonsulting",
    "Lofoya",
    "Ramped",
    "Jobflow",
    "Aragorn",
    "Careuka",
    "Jobmigo",
    "ApplyPass",
    "Final Round AI",
    "Pyjama Jobs",
    "Interview Warmup"
)

foreach ($comp in $competitors) {
    Write-Host "Generating content for $comp..."
    npx tsx scripts/seo/generate-competitor-content.ts "$comp"
    Start-Sleep -Seconds 2 # Gentle rate limiting
}
