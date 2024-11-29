$ComPort = "COM3"
$IsGitHubActions = $env:GITHUB_ACTIONS -eq 'true'

function Is-ComPortConnected($portName) {
    try {
        $port = [System.IO.Ports.SerialPort]::GetPortNames() -contains $portName
        return $port
    } catch {
        return $false
    }
}

# Set Python path dynamically
if ($IsGitHubActions) {
    $PythonPath = "${env:pythonLocation}\python.exe"
} else {
    $PythonPath = (Join-Path -Path (Get-Location) -ChildPath "..\TicTacToeSWPart\.venv\Scripts\python.exe")
}

# Move to the project directory
Set-Location -Path (Join-Path -Path $PSScriptRoot -ChildPath "..\TicTacToeSWPart")

$SkipHwTests = $IsGitHubActions -or !(Is-ComPortConnected -portName $ComPort)

Write-Output "Running software tests with pytest for detailed report and coverage..."

# Run software tests with coverage
& $PythonPath -m pytest --cov=main --cov-report=xml --cov-report=term-missing --junitxml=test-reports/results.xml "sw_tests.py"

if (-not $SkipHwTests) {
    Write-Output "COM port $ComPort detected. Running hardware tests..."
    & $PythonPath -m pytest --cov=main --cov-append --junitxml=test-reports/hw_results.xml "hw_tests.py"
} else {
    Write-Output "Skipping hardware tests."
}
