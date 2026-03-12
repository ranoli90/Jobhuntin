# JobHuntin Deployment Script with API Keys
# Run this in PowerShell

Write-Host "Configuring JobHuntin API Keys..."
Write-Host "=================================="

# Set environment variables
$env:LLM_API_KEY="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"
$env:JWT_SECRET="5ac9f551548b8c8eb2f45db7da24bec59e48039bf37daf8f988cbb2acde45ceec"
$env:CSRF_SECRET="f900e6e287d1da3c644b7121e9b68fb6035e7a9f829b8ce2e6fb"

Write-Host "✅ API Key configured"
Write-Host "✅ JWT Secret configured"
Write-Host "✅ CSRF Secret configured"

Write-Host ""
Write-Host "📋 Next Steps:"
Write-Host "1. Go to: https://dashboard.render.com"
Write-Host "2. Select: jobhuntin-api service"
Write-Host "3. Add Environment Variables:"
Write-Host "   - LLM_API_KEY: $env:LLM_API_KEY"
Write-Host "   - JWT_SECRET: $env:JWT_SECRET"
Write-Host "   - CSRF_SECRET: $env:CSRF_SECRET"
Write-Host "   - Set all to sync: false"
Write-Host "4. Click Save Changes"
Write-Host "5. Monitor deployment logs"

Write-Host ""
Write-Host "🔍 Testing API startup..."
$env:PYTHONPATH="apps:packages:."; python -c "
from api.main import app
print('✅ API should start successfully now!')
"

Write-Host ""
Write-Host "🌐 Checking API health..."
Start-Sleep -Seconds 10
try {
    $response = Invoke-WebRequest -Uri 'https://sorce-api.onrender.com/health' -UseBasicParsing $false -TimeoutSec 10
    $statusCode = $response.StatusCode
    Write-Host "API Status: $statusCode"
    
    if ($statusCode -eq 200) {
        Write-Host "🎉 DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
        Write-Host "🌐 API: https://sorce-api.onrender.com" -ForegroundColor Green
    } else {
        Write-Host "❌ API not responding (HTTP $statusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ Configuration complete!"
