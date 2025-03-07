# PowerShell script to upload ChromaDB data to S3
# Usage: .\upload_chroma_to_s3.ps1 [bucket-name] [environment]

param (
    [string]$BucketName = "conversational-resume",
    [string]$Environment = "production"
)

# Set variables
$Timestamp = Get-Date -Format "yyyyMMddHHmmss"
$ChromaDir = "data/chroma"
$ZipFile = "chroma_data_${Environment}_${Timestamp}.zip"

# Check if AWS CLI is installed
try {
    aws --version
} catch {
    Write-Error "AWS CLI is not installed. Please install it first."
    exit 1
}

# Check if the ChromaDB directory exists
if (-not (Test-Path $ChromaDir)) {
    Write-Error "ChromaDB directory not found at $ChromaDir"
    exit 1
}

Write-Host "Creating zip archive of ChromaDB data..."
# Use Compress-Archive which is built into PowerShell
Compress-Archive -Path $ChromaDir -DestinationPath $ZipFile -Force

Write-Host "Uploading to S3..."
aws s3 cp $ZipFile "s3://${BucketName}/chroma_data/${Environment}/${ZipFile}"

# Also upload to a fixed location for latest version
aws s3 cp $ZipFile "s3://${BucketName}/chroma_data/${Environment}/latest.zip"

Write-Host "Cleaning up..."
Remove-Item $ZipFile

Write-Host "Done! ChromaDB data uploaded to:"
Write-Host "s3://${BucketName}/chroma_data/${Environment}/${ZipFile}"
Write-Host "s3://${BucketName}/chroma_data/${Environment}/latest.zip" 