import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../storage/token_storage.dart';
import 'api_client.dart';

/// Armazenamento seguro compartilhado do token de acesso.
final tokenStorageProvider = Provider<TokenStorage>((ref) => TokenStorage());

/// Evento disparado quando uma chamada autenticada recebe HTTP 401.
final unauthorizedSignalProvider = Provider<StreamController<void>>((ref) {
  final controller = StreamController<void>.broadcast();
  ref.onDispose(controller.close);
  return controller;
});

/// Cliente HTTP compartilhado entre todos os repositorios do aplicativo.
final apiClientProvider = Provider<ApiClient>((ref) {
  final tokenStorage = ref.watch(tokenStorageProvider);
  final unauthorizedSignal = ref.watch(unauthorizedSignalProvider);
  return ApiClient(
    tokenStorage: tokenStorage,
    onUnauthorized: () async {
      if (!unauthorizedSignal.isClosed) {
        unauthorizedSignal.add(null);
      }
    },
  );
});
