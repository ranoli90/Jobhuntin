# Fix import paths from backend.domain to packages.backend.domain
Get-ChildItem -Recurse -Filter "*.py" | ForEach-Object {
    $content = Get-Content $_.FullName -Raw
    $original = $content
    
    # Replace all occurrences of "from backend.domain" with "from packages.backend.domain"
    $content = $content -replace 'from backend\.domain', 'from packages.backend.domain'
    
    # Only write if content changed
    if ($content -ne $original) {
        Set-Content $_.FullName $content -NoNewline
        Write-Host "Fixed imports in $($_.FullName)"
    }
}

Write-Host "Import path fixing complete!"
