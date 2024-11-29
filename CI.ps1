# Use UTF-8 encoding
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding

# ------------------------- CONFIGURABLE VARIABLES -----------------------------------------
$board = "arduino:avr:nano:cpu=atmega328old"
$baudRate = 9600
$sketch = "C:\Users\onisk\Desktop\csad2425ki401onyskomm15\Server\TicTacToe\TicTacToe.ino"
$serialLog = "serial_output.log"
# ------------------------------------------------------------------------------------------

function Check-ArduinoCLI {
    if (-not (Get-Command arduino-cli -ErrorAction SilentlyContinue)) {
        Write-Host "arduino-cli не знайдено. Будь ласка, встановіть його." -ForegroundColor Red
        exit 1
    }
}

function Select-ArduinoPort {
    Write-Host "Доступні порти:" -ForegroundColor Cyan
    
    try {
        $ports = & arduino-cli board list | Select-Object -Skip 1 | ForEach-Object { 
            ($_ -split '\s+')[0]
        }
        
        if (-not $ports) {
            Write-Host "Не знайдено доступних портів. Перевірте підключення плати." -ForegroundColor Red
            exit 1
        }
        
        for ($i = 0; $i -lt $ports.Count; $i++) {
            Write-Host "$i - $($ports[$i])" -ForegroundColor Green
        }

        do {
            $portNumber = Read-Host "Виберіть номер порту для вашої плати Arduino Nano"
        } while (-not ($portNumber -match '^\d+$' -and $portNumber -ge 0 -and $portNumber -lt $ports.Count))

        $global:port = $ports[$portNumber]
        Write-Host "Обраний порт: $global:port" -ForegroundColor Cyan
    }
    catch {
        Write-Host "Помилка при виборі порту: $_" -ForegroundColor Red
        exit 1
    }
}

function Compile-Sketch {
    Write-Host "Компіляція скетчу..." -ForegroundColor Cyan
    & arduino-cli compile --fqbn $board $sketch
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Помилка компіляції." -ForegroundColor Red
        exit 1
    }
    Write-Host "Компіляція успішна." -ForegroundColor Green
}

function Upload-Sketch {
    Write-Host "Завантаження скетчу на плату Arduino Nano через порт $global:port..." -ForegroundColor Cyan
    & arduino-cli upload -p $global:port --fqbn $board $sketch
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Помилка завантаження." -ForegroundColor Red
        exit 1
    }
    Write-Host "Завантаження успішне." -ForegroundColor Green
}

function Run-Tests {
    Write-Host "Виконання тестів..." -ForegroundColor Cyan

    try {
        $serialPort = New-Object System.IO.Ports.SerialPort $global:port, $baudRate
        $serialPort.Open()
        Start-Sleep -Seconds 2

        $serialPort.WriteLine('{"command":"RESET"}')
        Start-Sleep -Seconds 1
        $serialPort.WriteLine('{"command":"MOVE","row":0,"col":0}')
        Start-Sleep -Seconds 1
        $serialPort.WriteLine('{"command":"MOVE","row":1,"col":1}')

        $output = ""
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        while ($stopwatch.Elapsed.TotalSeconds -lt 5) {
            if ($serialPort.BytesToRead -gt 0) {
                $output += $serialPort.ReadExisting()
            }
        }
        $serialPort.Close()

        $output | Out-File -FilePath $serialLog -Encoding UTF8

        if ($output -match "TicTacToe Game Started" -and $output -match '"type":"board"') {
            Write-Host "Тести пройдені успішно." -ForegroundColor Green
        } else {
            Write-Host "Тести не пройдені. Перевірте лог виводу серійного порту." -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "Помилка під час виконання тестів: $_" -ForegroundColor Red
        exit 1
    }
}

# Головний блок виклику функцій
Check-ArduinoCLI
Select-ArduinoPort
Compile-Sketch
Upload-Sketch
Run-Tests2