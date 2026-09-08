# Aplicativo EcoTech

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
