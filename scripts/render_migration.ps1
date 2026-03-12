# Render Migration Script - Create Services on New Account
# API Key: rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF
# Owner ID: tea-d6p1rv6a2pns73f4sucg

$apiKey = "rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
$ownerId = "tea-d6p1rv6a2pns73f4sucg"
$baseUrl = "https://api.render.com/v1"

$headers = @{
    Authorization = "Bearer $apiKey"
    "Content-Type" = "application/json"
}

# Check current services
Write-Host "=== Current Services on New Account ===" -ForegroundColor Cyan
$services = Invoke-RestMethod -Uri "$baseUrl/services?ownerId=$ownerId" -Headers $headers
foreach ($svc in $services) {
    Write-Host "$($svc.service.name): $($svc.service.id) - $($svc.service.type)"
}

# Create jobhuntin-web static site
Write-Host "`n=== Creating jobhuntin-web static site ===" -ForegroundColor Cyan

# First, get VITE_API_URL from existing env or set a default
$apiUrl = "https://jobhuntin-api.onrender.com"

$webBody = @{
    type = "static_site"
    name = "jobhuntin-web"
    ownerId = $ownerId
    repo = "https://github.com/ranoli90/sorce"
    branch = "main"
    rootDir = "apps/web"
    serviceDetails = @{
        buildCommand = "npm ci && npx vite build"
        publishPath = "dist"
    }
    envVars = @(
        @{key = "VITE_API_URL"; value = $apiUrl}
    )
} | ConvertTo-Json -Depth 10

try {
    $webResponse = Invoke-RestMethod -Uri "$baseUrl/services" -Method Post -Headers $headers -Body $webBody
    Write-Host "Created: $($webResponse.name) - $($webResponse.id)" -ForegroundColor Green
} catch {
    Write-Host "Error creating web: $($_.Exception.Message)" -ForegroundColor Red
    $errorDetail = $_.Exception.Response
    if ($errorDetail) {
        $reader = New-Object System.IO.StreamReader($errorDetail.GetResponseStream())
        $body = $reader.ReadToEnd()
        Write-Host "Response: $body" -ForegroundColor Yellow
    }
}
