[CmdletBinding()]
param(
    [string]$DeviceId,
    [ValidateRange(1, 65535)]
    [int]$ApiPort = 5000,
    [ValidateNotNullOrEmpty()]
    [ValidateRange(1, 65535)]
    [int[]]$Ports = @(5599, 5000),
    [switch]$ForwardOnly,
    # Retained for compatibility: running the app is now the default.
    [switch]$RunApp
)

$ErrorActionPreference = 'Stop'
$mobileRoot = Split-Path -Parent $PSScriptRoot

$adbCommand = Get-Command adb -ErrorAction SilentlyContinue
$adbPath = if ($adbCommand) {
    $adbCommand.Source
} else {
    Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
}

if (-not (Test-Path -LiteralPath $adbPath)) {
    throw 'ADB nao encontrado. Instale o Android SDK Platform-Tools.'
}

$deviceLines = @(& $adbPath devices)
if ($LASTEXITCODE -ne 0) { throw 'Falha ao consultar os dispositivos ADB.' }
$devices = @($deviceLines | ForEach-Object {
    if ($_ -match '^(\S+)\s+device$') { $Matches[1] }
})
if ($devices.Count -eq 0) {
    throw 'Nenhum celular autorizado. Conecte o USB, ative a depuracao USB e aceite a autorizacao no aparelho.'
}

if ($DeviceId) {
    if ($DeviceId -notin $devices) { throw "Dispositivo nao autorizado ou ausente: $DeviceId" }
} elseif ($devices.Count -eq 1) {
    $DeviceId = $devices[0]
} else {
    throw "Informe -DeviceId. Dispositivos disponiveis: $($devices -join ', ')"
}

foreach ($port in (@($Ports) + @($ApiPort) | Sort-Object -Unique)) {
    & $adbPath -s $DeviceId reverse "tcp:$port" "tcp:$port"
    if ($LASTEXITCODE -ne 0) { throw "Falha ao encaminhar a porta $port." }
    Write-Host "Android localhost:$port -> computador localhost:$port"
}
& $adbPath -s $DeviceId reverse --list
if ($LASTEXITCODE -ne 0) { throw 'Falha ao verificar os encaminhamentos.' }

if ($ForwardOnly) {
    Write-Host 'Portas configuradas. O endereco gravado no app instalado NAO foi alterado.'
    Write-Host "Previa web: http://localhost:$($Ports[0])/ (servidor precisa estar ativo no PC)."
    return
}

$apiConnection = New-Object System.Net.Sockets.TcpClient
try {
    $pending = $apiConnection.ConnectAsync('127.0.0.1', $ApiPort)
    if (-not $pending.Wait(3000) -or -not $apiConnection.Connected) {
        throw 'Porta indisponivel.'
    }
} catch {
    throw "Backend indisponivel em localhost:$ApiPort. Inicie o servidor no PC antes de executar o app."
} finally {
    $apiConnection.Dispose()
}

$flutter = Get-Command flutter -ErrorAction SilentlyContinue
if (-not $flutter) { throw 'Flutter nao encontrado no PATH.' }
Write-Host "Executando o app com ECOTECH_API_BASE_URL=http://localhost:$ApiPort"
Write-Host 'Mantenha o servidor e a conexao USB ativos. Reexecute este script apos reconectar.'
Push-Location $mobileRoot
try {
    & $flutter.Source run -d $DeviceId "--dart-define=ECOTECH_API_BASE_URL=http://localhost:$ApiPort"
    if ($LASTEXITCODE -ne 0) { throw 'Flutter encerrou com erro.' }
} finally {
    Pop-Location
}
