# PowerShell script to trigger Render deployment
$headers = @{
    "Accept" = "application/json"
    "Authorization" = "Bearer rnd_60sCKrELEJ54xsuJYPR9Q1DalWxa"
}

$body = @{
    "clearCache" = $true
} | ConvertTo-Json

# Deploy web service
Write-Host "🚀 Deploying web service..."
try {
    $response = Invoke-RestMethod -Uri "https://api.render.com/v1/services/srv-cqdq7bg8fa8c73c1qgr0/deploys" -Method Post -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "✅ Web service deployment triggered"
} catch {
    Write-Host "⚠️  Web service deployment: $($_.Exception.Message)"
}

# Deploy SEO worker service
Write-Host "🚀 Deploying SEO worker service..."
try {
    $response = Invoke-RestMethod -Uri "https://api.render.com/v1/services/srv-cqdq7t68fa8c73c1qgs0/deploys" -Method Post -Headers $headers -Body $body -ContentType "application/json"
    Write-Host "✅ SEO worker service deployment triggered"
} catch {
    Write-Host "⚠️  SEO worker service deployment: $($_.Exception.Message)"
}

Write-Host "🎉 Deployment requests sent!"