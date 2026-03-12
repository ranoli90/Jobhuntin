$body = @{
    service = @{
        name = "jobhuntin-admin"
        type = "static_site"
        ownerID = "tea-d6p1rv6a2pns73f4sucg"
        repo = "https://github.com/ranoli90/sorce"
        branch = "main"
        rootDir = "apps/web-admin"
        buildCommand = "npm install && npm run build"
        publishPath = "dist"
        autoDeploy = "yes"
        envVars = @(
            @{key = "VITE_API_URL"; value = "https://jobhuntin-api.onrender.com"},
            @{key = "NODE_VERSION"; value = "20"}
        )
    }
} | ConvertTo-Json -Depth 5

Write-Host "Sending JSON:"
Write-Host $body

$response = Invoke-RestMethod -Uri "https://api.render.com/v1/services" -Method Post -Headers @{
    "Authorization" = "Bearer rnd_UiMNNzGNDphD0fyZsatrlHwM5QfF"
    "Content-Type" = "application/json"
    "Accept" = "application/json"
} -Body $body

$response | ConvertTo-Json -Depth 5
