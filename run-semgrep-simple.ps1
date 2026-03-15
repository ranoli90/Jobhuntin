# Simple Semgrep Security Audit Script for PowerShell
# Usage: .\run-semgrep-simple.ps1 [security|quality|full]

param(
    [Parameter(Position=0)]
    [ValidateSet("security", "quality", "full")]
    [string]$ScanType = "full"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ReportDir = Join-Path $ScriptDir "audit-reports"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Create reports directory
if (-not (Test-Path $ReportDir)) {
    New-Item -ItemType Directory -Path $ReportDir | Out-Null
}

Write-Host "====================================" -ForegroundColor Blue
Write-Host "Semgrep Security Audit Tool" -ForegroundColor Blue
Write-Host "====================================" -ForegroundColor Blue
Write-Host "Report directory: $ReportDir"
Write-Host "Timestamp: $Timestamp"
Write-Host ""

# Check if semgrep is installed
try {
    $null = Get-Command semgrep -ErrorAction Stop
} catch {
    Write-Host "❌ Semgrep not found. Please install it first:" -ForegroundColor Red
    Write-Host "pip install semgrep"
    exit 1
}

switch ($ScanType) {
    "security" {
        Write-Host "Running Security-Focused Audit..." -ForegroundColor Blue
        Write-Host ""
        
        $config = "p/security-audit,p/secrets,p/sql-injection,p/command-injection,p/xss"
        $outputFile = Join-Path $ReportDir "security-audit_$Timestamp.json"
        
        Write-Host "Running: Security Rules (OWASP Top 10, Secrets, Injection)"
        $result = semgrep --config=$config --json --output=$outputFile . 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Scan completed successfully" -ForegroundColor Green
            Write-Host "📊 Report saved to: $outputFile"
        } else {
            Write-Host "❌ Scan failed" -ForegroundColor Red
            Write-Host $result
        }
    }
    
    "quality" {
        Write-Host "Running Code Quality Audit..." -ForegroundColor Blue
        Write-Host ""
        
        $config = "p/bandit,p/flask,p/django"
        $outputFile = Join-Path $ReportDir "quality-audit_$Timestamp.json"
        
        Write-Host "Running: Code Quality Rules"
        $result = semgrep --config=$config --json --output=$outputFile . 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Scan completed successfully" -ForegroundColor Green
            Write-Host "📊 Report saved to: $outputFile"
        } else {
            Write-Host "❌ Scan failed" -ForegroundColor Red
            Write-Host $result
        }
    }
    
    "full" {
        Write-Host "Running Comprehensive Full Audit..." -ForegroundColor Blue
        Write-Host ""
        
        # Security scan
        $securityConfig = "p/security-audit,p/secrets,p/sql-injection,p/command-injection,p/xss"
        $securityOutput = Join-Path $ReportDir "security_$Timestamp.json"
        
        Write-Host "Running: Security Rules"
        $result = semgrep --config=$securityConfig --json --output=$securityOutput . 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Security scan completed" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Security scan had issues" -ForegroundColor Yellow
        }
        
        # Python security scan
        $pythonConfig = "p/bandit,p/flask,p/django,p/sql-injection"
        $pythonOutput = Join-Path $ReportDir "python-security_$Timestamp.json"
        
        Write-Host "Running: Python Security Rules"
        $result = semgrep --config=$pythonConfig --json --output=$pythonOutput . 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Python security scan completed" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Python security scan had issues" -ForegroundColor Yellow
        }
        
        # Create summary
        $summaryFile = Join-Path $ReportDir "summary_$Timestamp.txt"
        "Semgrep Audit Summary" | Out-File -FilePath $summaryFile
        "Timestamp: $(Get-Date)" | Out-File -FilePath $summaryFile -Append
        "Scan Type: Full Comprehensive Audit" | Out-File -FilePath $summaryFile -Append
        "" | Out-File -FilePath $summaryFile -Append
        "Reports Generated:" | Out-File -FilePath $summaryFile -Append
        "- Security JSON Data: security_$Timestamp.json" | Out-File -FilePath $summaryFile -Append
        "- Python Security JSON Data: python-security_$Timestamp.json" | Out-File -FilePath $summaryFile -Append
        "" | Out-File -FilePath $summaryFile -Append
        "Quick Actions:" | Out-File -FilePath $summaryFile -Append
        "1. Review high-severity findings first" | Out-File -FilePath $summaryFile -Append
        "2. Address security vulnerabilities immediately" | Out-File -FilePath $summaryFile -Append
        "3. Create tickets for medium/low priority issues" | Out-File -FilePath $summaryFile -Append
        "4. Update code to prevent future occurrences" | Out-File -FilePath $summaryFile -Append
        
        Write-Host "✅ Full audit completed!" -ForegroundColor Green
        Write-Host "📊 Summary report: $summaryFile" -ForegroundColor Green
        Write-Host "📁 All reports saved to: $ReportDir" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Blue
Write-Host "Audit Complete" -ForegroundColor Blue
Write-Host "====================================" -ForegroundColor Blue
Write-Host "✅ All reports saved to: $ReportDir" -ForegroundColor Green
Write-Host ""
Write-Host "Latest Reports:"
Get-ChildItem -Path $ReportDir -Filter "*$Timestamp*" | ForEach-Object {
    Write-Host "  $($_.Name)"
}
Write-Host ""
Write-Host "To view JSON reports, open them in VS Code or use:"
Write-Host "Get-Content '$ReportDir\security_$Timestamp.json' | ConvertFrom-Json"
