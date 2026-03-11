# PowerShell script to trigger Render deployment
# Requires: RENDER_API_KEY. Optionally RENDER_SERVICE_ID_WEB, RENDER_SERVICE_ID_SEO (override defaults per environment)
$apiKey = $env:RENDER_API_KEY
if (-not $apiKey) {
    Write-Error "Set RENDER_API_KEY environment variable"
    exit 1
}
# Service IDs from Render Dashboard - set env vars to override for your environment
$webServiceId = if ($env:RENDER_SERVICE_ID_WEB) { $env:RENDER_SERVICE_ID_WEB } else { "srv-cqdq7bg8fa8c73c1qgr0" }
$seoServiceId = if ($env:RENDER_SERVICE_ID_SEO) { $env:RENDER_SERVICE_ID_SEO } else { "srv-cqdq7t68fa8c73c1qgs0" }
$headers = @{
    "Accept" = "application/json"
    "Authorization" = "Bearer $apiKey"
}

$body = @{
    "clearCache" = $true
} | ConvertTo-Json

# Deploy web service
Write-Host "🚀 Deploying web service..."
try {
    $response = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$webServiceId/deploys" -Method Post -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "✅ Web service deployment triggered"
} catch {
    Write-Host "⚠️  Web service deployment: $($_.Exception.Message)"
}

# Deploy SEO worker service
Write-Host "🚀 Deploying SEO worker service..."
try {
    $response = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$seoServiceId/deploys" -Method Post -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "✅ SEO worker service deployment triggered"
} catch {
    Write-Host "⚠️  SEO worker service deployment: $($_.Exception.Message)"
}

Write-Host "🎉 Deployment requests sent!"