# Upload E2E Test Screenshots to Server
# Run this script on Windows machine where Playwright MCP client runs
# Date: 2025-10-12

$PlaywrightTempBase = "$env:LOCALAPPDATA\Temp\playwright-mcp-output"
$ServerUser = "flip"
$ServerHost = "192.168.1.30"
$ServerPath = "/home/flip/agent-forge/media"

Write-Host "🔍 Searching for E2E test screenshots..." -ForegroundColor Cyan
Write-Host ""

# Find all playwright sessions
$sessions = Get-ChildItem -Path $PlaywrightTempBase -Directory -ErrorAction SilentlyContinue

if ($sessions) {
    Write-Host "Found $($sessions.Count) Playwright session(s)" -ForegroundColor Green
    
    foreach ($session in $sessions) {
        $mediaPath = Join-Path $session.FullName "media"
        
        if (Test-Path $mediaPath) {
            $screenshots = Get-ChildItem -Path $mediaPath -Filter "e2e-test-*.png" -ErrorAction SilentlyContinue
            
            if ($screenshots) {
                Write-Host ""
                Write-Host "📸 Found $($screenshots.Count) screenshot(s) in session: $($session.Name)" -ForegroundColor Yellow
                
                foreach ($screenshot in $screenshots) {
                    Write-Host "   - $($screenshot.Name) ($([math]::Round($screenshot.Length/1KB, 2)) KB)"
                }
                
                Write-Host ""
                Write-Host "📤 Uploading to server..." -ForegroundColor Cyan
                
                # Use SCP to copy files
                foreach ($screenshot in $screenshots) {
                    $scpCommand = "scp `"$($screenshot.FullName)`" ${ServerUser}@${ServerHost}:${ServerPath}/"
                    Write-Host "Executing: $scpCommand" -ForegroundColor Gray
                    
                    # Check if SCP is available
                    $scpExists = Get-Command scp -ErrorAction SilentlyContinue
                    
                    if ($scpExists) {
                        scp "$($screenshot.FullName)" "${ServerUser}@${ServerHost}:${ServerPath}/"
                        
                        if ($LASTEXITCODE -eq 0) {
                            Write-Host "   ✅ Uploaded: $($screenshot.Name)" -ForegroundColor Green
                        } else {
                            Write-Host "   ❌ Failed to upload: $($screenshot.Name)" -ForegroundColor Red
                        }
                    } else {
                        Write-Host ""
                        Write-Host "⚠️  SCP not found. Install OpenSSH Client:" -ForegroundColor Yellow
                        Write-Host "   Settings > Apps > Optional Features > OpenSSH Client" -ForegroundColor Gray
                        Write-Host ""
                        Write-Host "Alternative: Use WinSCP or manual copy:" -ForegroundColor Yellow
                        Write-Host "   Source: $($screenshot.FullName)"
                        Write-Host "   Destination: ${ServerUser}@${ServerHost}:${ServerPath}/"
                        break
                    }
                }
            }
        }
    }
    
    Write-Host ""
    Write-Host "✅ Done!" -ForegroundColor Green
    
} else {
    Write-Host "❌ No Playwright sessions found in:" -ForegroundColor Red
    Write-Host "   $PlaywrightTempBase"
    Write-Host ""
    Write-Host "Make sure Playwright MCP has run and created screenshots." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
