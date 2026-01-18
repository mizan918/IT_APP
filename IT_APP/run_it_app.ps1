# Navigate to your IT_APP folder
Set-Location "D:\MizanurRahman321\IT_APP_PYTHON\IT_APP"

# --- Activate virtual environment ---
$venvPath = ".\venv\Scripts\Activate"
if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..."
    . $venvPath
} else {
    Write-Host "No virtual environment found. Make sure Python is installed."
}

# --- Install requirements ---
Write-Host "Installing/updating requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# --- Open firewall port 5000 ---
Write-Host "Opening firewall port 5000..."
New-NetFirewallRule -DisplayName "IT_APP_5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow

# --- Get local IP and display URL ---
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like "192.*" }).IPAddress
if (-not $ip) { $ip = "localhost" }
Write-Host "IT_APP will be accessible at: http://$ip:5000"

# --- Run app with Waitress ---
Write-Host "Starting IT_APP on LAN (0.0.0.0:5000)..."
python -m waitress --listen=0.0.0.0:5000 app:app
