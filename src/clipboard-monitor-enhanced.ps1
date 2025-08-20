# Enhanced Clipboard Monitor - Handles files and images
# Captures GIFs, images, and file references from clipboard

param(
    [string]$ProjectPath = (Get-Location).Path,
    [int]$MaxHistory = 20
)

# Load assemblies for clipboard access
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Convert WSL path if needed
if ($ProjectPath -match "^/mnt/([a-z])/(.*)") {
    $drive = $matches[1].ToUpper()
    $path = $matches[2] -replace "/", "\"
    $ProjectPath = "${drive}:\${path}"
}

# Ensure .claude/captures directory exists
$CapturesPath = Join-Path $ProjectPath ".claude\captures"
if (!(Test-Path $CapturesPath)) {
    New-Item -ItemType Directory -Path $CapturesPath -Force | Out-Null
    Write-Host "Created captures directory: $CapturesPath" -ForegroundColor Green
}

# Display startup info
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  ENHANCED CLIPBOARD MONITOR" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Project: " -NoNewline -ForegroundColor White
Write-Host $ProjectPath -ForegroundColor Green
Write-Host "Saving to: " -NoNewline -ForegroundColor White
Write-Host $CapturesPath -ForegroundColor Green
Write-Host "Mode: " -NoNewline -ForegroundColor White
Write-Host "Images + File References (GIFs!)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Yellow
Write-Host ""

# Initialize tracking
$lastImageHash = ""
$lastFilePath = ""
$captureCount = 0

# Initial delay
Start-Sleep -Milliseconds 500

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] " -NoNewline -ForegroundColor DarkGray
Write-Host "READY " -NoNewline -ForegroundColor Green
Write-Host "- Monitoring clipboard for images and files..." -ForegroundColor DarkGray

# Main monitoring loop
while ($true) {
    try {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $displayTime = Get-Date -Format "HH:mm:ss"
        
        # Get clipboard data object
        $dataObject = [System.Windows.Forms.Clipboard]::GetDataObject()
        
        if ($dataObject) {
            # Check for file references (GIFs from ShareX, etc.)
            if ($dataObject.GetDataPresent("FileDrop")) {
                $files = $dataObject.GetData("FileDrop")
                
                foreach ($file in $files) {
                    # Check if it's an image/gif file
                    if ($file -match "\.(gif|png|jpg|jpeg|bmp|tiff|webp)$") {
                        if ($file -ne $lastFilePath -and (Test-Path $file)) {
                            $fileInfo = Get-Item $file
                            $extension = $fileInfo.Extension.TrimStart('.')
                            
                            # Copy file to captures folder
                            $destFile = Join-Path $CapturesPath "img_$timestamp.$extension"
                            Copy-Item $file $destFile -Force
                            
                            # Get file size for display
                            $fileSize = $fileInfo.Length
                            $sizeStr = if ($fileSize -gt 1MB) {
                                "{0:N1} MB" -f ($fileSize / 1MB)
                            } elseif ($fileSize -gt 1KB) {
                                "{0:N0} KB" -f ($fileSize / 1KB)
                            } else {
                                "$fileSize B"
                            }
                            
                            # Try to get image dimensions
                            $dimensions = "unknown"
                            try {
                                $img = [System.Drawing.Image]::FromFile($file)
                                $dimensions = "$($img.Width)×$($img.Height)"
                                $img.Dispose()
                            } catch {
                                # Couldn't get dimensions
                            }
                            
                            Write-Host "[$displayTime] " -NoNewline -ForegroundColor DarkGray
                            Write-Host "FILE " -NoNewline -ForegroundColor Cyan
                            Write-Host "→ " -NoNewline -ForegroundColor White
                            Write-Host "$dimensions " -NoNewline -ForegroundColor Green
                            Write-Host "$($extension.ToUpper()) " -NoNewline -ForegroundColor Magenta
                            Write-Host "($sizeStr) " -NoNewline -ForegroundColor DarkGray
                            Write-Host "→ img_$timestamp.$extension" -ForegroundColor Yellow
                            
                            $lastFilePath = $file
                            $captureCount++
                        }
                    }
                }
            }
            # Also check for direct image data (screenshots, etc.)
            elseif ($dataObject.GetDataPresent([System.Drawing.Bitmap])) {
                $currentImage = $dataObject.GetData([System.Drawing.Bitmap])
                
                if ($currentImage) {
                    # Create hash to detect changes
                    $pixelSample = ""
                    try {
                        $pixelSample = "$($currentImage.GetPixel(0,0).ToArgb())"
                        $pixelSample += "_$($currentImage.GetPixel($currentImage.Width-1,0).ToArgb())"
                        $pixelSample += "_$($currentImage.GetPixel(0,$currentImage.Height-1).ToArgb())"
                        $pixelSample += "_$($currentImage.GetPixel([int]($currentImage.Width/2),[int]($currentImage.Height/2)).ToArgb())"
                    } catch {
                        $pixelSample = $currentImage.GetHashCode()
                    }
                    
                    $imageHash = "$($currentImage.Width)x$($currentImage.Height)_$pixelSample"
                    
                    if ($imageHash -ne $lastImageHash) {
                        # Save as PNG (screenshots are usually PNG)
                        $imageFile = Join-Path $CapturesPath "img_$timestamp.png"
                        $currentImage.Save($imageFile, [System.Drawing.Imaging.ImageFormat]::Png)
                        
                        # Get file size
                        $fileSize = (Get-Item $imageFile).Length
                        $sizeStr = if ($fileSize -gt 1MB) {
                            "{0:N1} MB" -f ($fileSize / 1MB)
                        } elseif ($fileSize -gt 1KB) {
                            "{0:N0} KB" -f ($fileSize / 1KB)
                        } else {
                            "$fileSize B"
                        }
                        
                        Write-Host "[$displayTime] " -NoNewline -ForegroundColor DarkGray
                        Write-Host "IMAGE " -NoNewline -ForegroundColor Green
                        Write-Host "→ " -NoNewline -ForegroundColor White
                        Write-Host "$($currentImage.Width)×$($currentImage.Height) " -NoNewline -ForegroundColor Cyan
                        Write-Host "PNG " -NoNewline -ForegroundColor Magenta
                        Write-Host "($sizeStr) " -NoNewline -ForegroundColor DarkGray
                        Write-Host "→ img_$timestamp.png" -ForegroundColor Yellow
                        
                        $lastImageHash = $imageHash
                        $lastFilePath = ""  # Clear file path when we get image data
                        $captureCount++
                    }
                }
            }
        }
        
        # Cleanup old files periodically
        if ($captureCount % 10 -eq 0 -and $captureCount -gt 0) {
            $allFiles = Get-ChildItem (Join-Path $CapturesPath "img_*") -File | 
                       Sort-Object LastWriteTime -Descending
            
            if ($allFiles.Count -gt $MaxHistory) {
                $toDelete = $allFiles | Select-Object -Skip $MaxHistory
                $deleteCount = $toDelete.Count
                $toDelete | Remove-Item -Force
                
                if ($deleteCount -gt 0) {
                    Write-Host "[$displayTime] " -NoNewline -ForegroundColor DarkGray
                    Write-Host "CLEANUP " -NoNewline -ForegroundColor Magenta
                    Write-Host "→ Removed $deleteCount old items" -ForegroundColor DarkGray
                }
            }
        }
        
        # Sleep to prevent high CPU usage
        Start-Sleep -Milliseconds 500
        
    } catch {
        # Continue on errors
        Start-Sleep -Milliseconds 1000
    }
}