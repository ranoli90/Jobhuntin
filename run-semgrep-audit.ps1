# Semgrep Security Audit Script for PowerShell
# Usage: .\run-semgrep-audit.ps1 [security|quality|full|custom]

param(
    [Parameter(Position=0)]
    [ValidateSet("security", "quality", "full", "custom")]
    [string]$ScanType = "full",
    
    [Parameter(Position=1)]
    [string]$CustomConfig = ""
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ReportDir = Join-Path $ScriptDir "audit-reports"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Create reports directory
if (-not (Test-Path $ReportDir)) {
    New-Item -ItemType Directory -Path $ReportDir | Out-Null
}

# Color functions
function Write-Header {
    param([string]$Text)
    Write-Host "====================================" -ForegroundColor Blue
    Write-Host $Text -ForegroundColor Blue
    Write-Host "====================================" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Text)
    Write-Host "⚠️  $Text" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor Red
}

# Function to run Semgrep
function Invoke-Semgrep {
    param(
        [string]$Config,
        [string]$OutputFile,
        [string]$Description
    )
    
    Write-Header "Running: $Description"
    
    try {
        $result = semgrep --config=$Config --json --output=$OutputFile . 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Scan completed successfully"
            
            if (Test-Path $OutputFile) {
                try {
                    $json = Get-Content $OutputFile | ConvertFrom-Json
                    $findings = $json.results.Count
                    $rules = $json.rules.Count
                    
                    Write-Host "📊 Findings: $findings | Rules: $rules"
                    
                    if ($findings -gt 0) {
                        Write-Warning "$findings issues found - check report for details"
                    } else {
                        Write-Success "No issues found!"
                    }
                } catch {
                    Write-Warning "Could not parse JSON results"
                }
            }
        } else {
            Write-Error "Scan failed with exit code $LASTEXITCODE"
            Write-Host $result
            return $false
        }
    } catch {
        Write-Error "Exception occurred: $_"
        return $false
    }
    
    Write-Host ""
    return $true
}

# Main execution
Write-Header "Semgrep Security Audit Tool"
Write-Host "Report directory: $ReportDir"
Write-Host "Timestamp: $Timestamp"
Write-Host ""

# Check if semgrep is installed
try {
    $null = Get-Command semgrep -ErrorAction Stop
} catch {
    Write-Error "Semgrep not found. Please install it first:"
    Write-Host "pip install semgrep"
    exit 1
}

switch ($ScanType) {
    "security" {
        Write-Header "Security-Focused Audit"
        
        $config = "p/security-audit,p/secrets,p/sql-injection,p/command-injection,p/xss"
        $outputFile = Join-Path $ReportDir "security-audit_$Timestamp.json"
        $description = "Security Rules (OWASP Top 10, Secrets, Injection)"
        
        if (Invoke-Semgrep -Config $config -OutputFile $outputFile -Description $description) {
            Write-Success "Security report generated: $outputFile"
        }
    }
    
    "quality" {
        Write-Header "Code Quality Audit"
        
        $config = "p/bandit,p/flask,p/django"
        $outputFile = Join-Path $ReportDir "quality-audit_$Timestamp.json"
        $description = "Code Quality Rules"
        
        if (Invoke-Semgrep -Config $config -OutputFile $outputFile -Description $description) {
            Write-Success "Quality report generated: $outputFile"
        }
    }
    
    "full" {
        Write-Header "Comprehensive Full Audit"
        
        # Security scan
        $securityConfig = "p/security-audit,p/secrets,p/sql-injection,p/command-injection,p/xss"
        $securityOutput = Join-Path $ReportDir "security_$Timestamp.json"
        
        if (Invoke-Semgrep -Config $securityConfig -OutputFile $securityOutput -Description "Security Rules") {
            # Python security scan
            $pythonConfig = "p/bandit,p/flask,p/django,p/sql-injection"
            $pythonOutput = Join-Path $ReportDir "python-security_$Timestamp.json"
            
            if (Invoke-Semgrep -Config $pythonConfig -OutputFile $pythonOutput -Description "Python Security Rules") {
                # Create summary report
                $summaryFile = Join-Path $ReportDir "summary_$Timestamp.md"
                
                $summary = @"
# Semgrep Audit Summary

**Timestamp:** $(Get-Date)
**Scan Type:** Full Comprehensive Audit

## Reports Generated
- Security JSON Data: security_$Timestamp.json
- Python Security JSON Data: python-security_$Timestamp.json

## Quick Actions
1. Review high-severity findings first
2. Address security vulnerabilities immediately
3. Create tickets for medium/low priority issues
4. Update code to prevent future occurrences

---
*Generated by Semgrep Audit Script*
"@
                
                $summary | Out-File -FilePath $summaryFile -Encoding UTF8
                
                Write-Success "Full audit completed!"
                Write-Success "Summary report: $summaryFile"
                Write-Success "HTML reports available in: $ReportDir/"
            }
        }
    }
    
    "custom" {
        if ([string]::IsNullOrEmpty($CustomConfig)) {
            Write-Error "Custom scan requires configuration argument"
            Write-Host "Usage: .\run-semgrep-audit.ps1 custom -CustomConfig 'p/security-audit,p/bandit'"
            exit 1
        }
        
        $outputFile = Join-Path $ReportDir "custom-audit_$Timestamp.json"
        $description = "Custom Configuration: $CustomConfig"
        
        if (Invoke-Semgrep -Config $CustomConfig -OutputFile $outputFile -Description $description) {
            Write-Success "Custom audit completed: $outputFile"
        }
    }
}

Write-Header "Audit Complete"
Write-Success "All reports saved to: $ReportDir"
Write-Host ""

Write-Host "Latest Reports:"
Get-ChildItem -Path $ReportDir -Filter "*$Timestamp*" | ForEach-Object {
    Write-Host "  $($_.Name)"
}

Write-Host ""
Write-Host "To view JSON reports, use a JSON viewer or:"
Write-Host "Get-Content '$ReportDir\security_$Timestamp.json' | ConvertFrom-Json | Select-Object -ExpandProperty results"
Write-Host ""
Write-Host "For detailed analysis, open the JSON files in a code editor like VS Code."
