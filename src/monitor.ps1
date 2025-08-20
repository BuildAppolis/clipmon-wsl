#!/usr/bin/env pwsh
# ClipmonWSL Monitor - Complete clipboard monitoring with references.json
# by BuildAppolis

param(
    [string]$ProjectPath = (Get-Location),
    [int]$MaxHistory = 50
)

# Setup paths
$CapturesPath = Join-Path $ProjectPath ".claude/captures"
$ReferencesFile = Join-Path $CapturesPath "references.json"

# Create captures directory if needed
if (-not (Test-Path $CapturesPath)) {
    New-Item -ItemType Directory -Path $CapturesPath -Force | Out-Null
}

# Initialize or load references
if (Test-Path $ReferencesFile) {
    $references = Get-Content $ReferencesFile -Raw | ConvertFrom-Json
    if (-not $references.numbered) {
        $references | Add-Member -NotePropertyName "numbered" -NotePropertyValue @{} -Force
    }
} else {
    $references = @{
        latest = ""
        numbered = @{}
        updated = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    }
}

# Get next capture number
$nextNumber = 1
if ($references.numbered -and $references.numbered.PSObject.Properties.Count -gt 0) {
    $maxKey = ($references.numbered.PSObject.Properties.Name | ForEach-Object { [int]$_ } | Measure-Object -Maximum).Maximum
    $nextNumber = $maxKey + 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CLIPMONWSL MONITOR" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: " -NoNewline -ForegroundColor Gray
Write-Host $ProjectPath -ForegroundColor Yellow
Write-Host "Saving to: " -NoNewline -ForegroundColor Gray
Write-Host $CapturesPath -ForegroundColor Yellow
Write-Host "Next capture: #$nextNumber" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Gray
Write-Host ""

$lastImageHash = ""
$lastFilePath = ""
$captureCount = $nextNumber - 1

function Save-References {
    param($refs, $file)
    
    # Update timestamp
    $refs.updated = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss.ffffff")
    
    # Convert to JSON and save
    $refs | ConvertTo-Json -Depth 10 | Set-Content -Path $file -Encoding UTF8
}

function Add-Capture {
    param(
        [string]$FilePath,
        [string]$FileName,
        [long]$Size,
        [int]$Number
    )
    
    $script:references.numbered["$Number"] = @{
        path = $FilePath
        name = $FileName
        size = $Size
        time = (Get-Date -Format "HH:mm:ss")
    }
    
    $script:references.latest = $FileName
    
    Save-References -refs $script:references -file $ReferencesFile
}

# Monitor loop
while ($true) {
    try {
        $clipData = Get-Clipboard -Format Image -ErrorAction SilentlyContinue
        
        if ($clipData) {
            # Handle image data
            $imageBytes = [System.IO.MemoryStream]::new()
            $clipData.Save($imageBytes, [System.Drawing.Imaging.ImageFormat]::Png)
            $imageData = $imageBytes.ToArray()
            
            # Create hash for comparison
            $hasher = [System.Security.Cryptography.SHA256]::Create()
            $imageHash = [BitConverter]::ToString($hasher.ComputeHash($imageData))
            
            if ($imageHash -ne $lastImageHash) {
                # New image detected
                $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
                $fileName = "img_$timestamp.png"
                $outputPath = Join-Path $CapturesPath $fileName
                
                # Save image
                [System.IO.File]::WriteAllBytes($outputPath, $imageData)
                $fileSize = (Get-Item $outputPath).Length
                
                # Update capture count and references
                $captureCount++
                Add-Capture -FilePath $outputPath -FileName $fileName -Size $fileSize -Number $captureCount
                
                # Display capture info
                $displayTime = Get-Date -Format "HH:mm:ss"
                $sizeKB = [math]::Round($fileSize / 1KB, 1)
                
                Write-Host "[$displayTime] " -NoNewline -ForegroundColor DarkGray
                Write-Host "IMAGE " -NoNewline -ForegroundColor Green
                Write-Host "#$captureCount " -NoNewline -ForegroundColor Cyan
                Write-Host "($sizeKB KB) " -NoNewline -ForegroundColor DarkGray
                Write-Host "→ $fileName" -ForegroundColor Yellow
                
                $lastImageHash = $imageHash
            }
        }
        
        # Check for file paths (GIFs)
        $textClip = Get-Clipboard -Format Text -ErrorAction SilentlyContinue
        if ($textClip -and $textClip -ne $lastFilePath) {
            if (Test-Path $textClip -PathType Leaf) {
                $file = Get-Item $textClip
                if ($file.Extension -in @('.gif', '.png', '.jpg', '.jpeg', '.bmp')) {
                    # Copy file to captures
                    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
                    $extension = $file.Extension
                    $fileName = "img_$timestamp$extension"
                    $outputPath = Join-Path $CapturesPath $fileName
                    
                    Copy-Item -Path $textClip -Destination $outputPath -Force
                    $fileSize = (Get-Item $outputPath).Length
                    
                    # Update capture count and references
                    $captureCount++
                    Add-Capture -FilePath $outputPath -FileName $fileName -Size $fileSize -Number $captureCount
                    
                    # Display capture info
                    $displayTime = Get-Date -Format "HH:mm:ss"
                    $sizeKB = [math]::Round($fileSize / 1KB, 1)
                    $fileType = if ($extension -eq '.gif') { "GIF" } else { "FILE" }
                    
                    Write-Host "[$displayTime] " -NoNewline -ForegroundColor DarkGray
                    Write-Host "$fileType " -NoNewline -ForegroundColor Magenta
                    Write-Host "#$captureCount " -NoNewline -ForegroundColor Cyan
                    Write-Host "($sizeKB KB) " -NoNewline -ForegroundColor DarkGray
                    Write-Host "→ $fileName" -ForegroundColor Yellow
                    
                    $lastFilePath = $textClip
                }
            }
        }
        
        # Cleanup old captures periodically
        if ($captureCount % 10 -eq 0 -and $captureCount -gt 0) {
            if ($references.numbered.PSObject.Properties.Count -gt $MaxHistory) {
                # Remove oldest entries
                $sortedKeys = $references.numbered.PSObject.Properties.Name | 
                              ForEach-Object { [int]$_ } | 
                              Sort-Object
                
                $toRemove = $sortedKeys | Select-Object -First ($sortedKeys.Count - $MaxHistory)
                
                foreach ($key in $toRemove) {
                    $entry = $references.numbered."$key"
                    if ($entry -and $entry.path -and (Test-Path $entry.path)) {
                        Remove-Item -Path $entry.path -Force -ErrorAction SilentlyContinue
                    }
                    $references.numbered.PSObject.Properties.Remove("$key")
                }
                
                Save-References -refs $references -file $ReferencesFile
                
                $displayTime = Get-Date -Format "HH:mm:ss"
                Write-Host "[$displayTime] " -NoNewline -ForegroundColor DarkGray
                Write-Host "CLEANUP " -NoNewline -ForegroundColor Magenta
                Write-Host "→ Removed $($toRemove.Count) old items" -ForegroundColor DarkGray
            }
        }
        
        # Sleep to prevent high CPU usage
        Start-Sleep -Milliseconds 500
        
    } catch {
        # Continue on errors
        Start-Sleep -Milliseconds 1000
    }
}