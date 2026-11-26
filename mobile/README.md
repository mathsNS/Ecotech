# Aplicativo EcoTech

## Celular Android usando o localhost do computador

Conecte o Android por USB, habilite **Depuração USB** nas opções de desenvolvedor
e aceite a autorização no celular. Na raiz do repositório, execute:

```powershell
powershell -ExecutionPolicy Bypass -File .\mobile\scripts\conectar-celular.ps1
```

O script encaminha as portas **5599** (prévia web) e **5000** (API) para o
computador usando `adb reverse`, verifica a porta da API e **executa o app nativo**
com `ECOTECH_API_BASE_URL=http://localhost:5000`. Os servidores precisam estar
rodando no PC; o script não os inicia.
Não é necessário expor o servidor à rede Wi-Fi ou alterar o firewall.

Para apenas encaminhar as portas, sem recompilar ou abrir o app:

```powershell
powershell -ExecutionPolicy Bypass -File .\mobile\scripts\conectar-celular.ps1 -ForwardOnly
```

Nesse modo, abra **http://localhost:5599/** no navegador do celular. O parâmetro
`-RunApp` continua aceito, mas executar o app já é o comportamento padrão.

**Importante:** `adb reverse` sozinho não altera o endereço de um APK instalado.
`10.0.2.2` é o endereço do computador no emulador Android, não no celular físico.
A variável correta é `ECOTECH_API_BASE_URL`; `API_BASE_URL` não é lida pelo app.
Após recompilar com outro endereço, use novamente este script para voltar à
configuração USB. Não é necessário apagar dados ou fazer logout.

Com vários dispositivos conectados, informe `-DeviceId SERIAL`. Outras portas
podem ser informadas ao chamar o script pelo PowerShell:

```powershell
.\mobile\scripts\conectar-celular.ps1 -DeviceId SERIAL -Ports 5599,5000,8080
```

Funciona também com Android já conectado ao ADB por **depuração sem fio**.
Mantenha a conexão ADB ativa e execute novamente após reconectar o aparelho.
Para remover um encaminhamento: `adb -s SERIAL reverse --remove tcp:5599`
(repita para a porta 5000, se necessário).

O encaminhamento ADB não funciona no iPhone. Nesse caso, use o IP local do PC,
com ambos na mesma rede e os servidores escutando na interface de rede
(`0.0.0.0`), em vez de `localhost`.

## Endereço da API

O aplicativo usa automaticamente `http://localhost:5000` no Flutter Web e
`http://10.0.2.2:5000` no emulador Android.

Para executar em um dispositivo físico ou apontar para outro ambiente, informe
o endereço do backend explicitamente:

```powershell
flutter run --dart-define=ECOTECH_API_BASE_URL=http://192.168.0.10:5000
```

O backend pode ser iniciado na raiz do repositório:

```powershell
docker compose up --build
```
