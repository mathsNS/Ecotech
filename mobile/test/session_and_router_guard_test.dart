import 'dart:async';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:ecotech_mobile/core/api/api_client.dart';
import 'package:ecotech_mobile/core/api/api_providers.dart';
import 'package:ecotech_mobile/core/router/app_router.dart';
import 'package:ecotech_mobile/core/storage/token_storage.dart';
import 'package:ecotech_mobile/data/auth/auth_repository.dart';
import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/data/dashboard/dashboard_data.dart';
import 'package:ecotech_mobile/data/dashboard/dashboard_repository.dart';
import 'package:ecotech_mobile/data/finance/finance_data.dart';
import 'package:ecotech_mobile/data/finance/finance_repository.dart';
import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:ecotech_mobile/features/auth/auth_controller.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:ecotech_mobile/features/dashboard/dashboard_controller.dart';
import 'package:ecotech_mobile/features/finance/finance_controller.dart';
import 'package:ecotech_mobile/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _MemoriaTokenStorage extends TokenStorage {
  String? valor;
  int limpezas = 0;

  @override
  Future<void> salvar(String token) async {
    valor = token;
  }

  @override
  Future<String?> ler() async => valor;

  @override
  Future<void> limpar() async {
    valor = null;
    limpezas++;
  }
}

class _StatusAdapter implements HttpClientAdapter {
  _StatusAdapter(this.statusCode);

  final int statusCode;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    return ResponseBody.fromString(
      '{"erro": "Sessao expirada"}',
      statusCode,
      headers: {
        Headers.contentTypeHeader: ['application/json'],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

class _FakeAuthRepository implements AuthRepository {
  _FakeAuthRepository({this.atual});

  Usuario? atual;
  int logouts = 0;

  @override
  Future<Usuario?> usuarioAtual() async => atual;

  @override
  Future<Usuario> login({
    required String tipo,
    required String credencial,
    required String senha,
  }) async {
    atual = Usuario(
      id: 'user-$credencial',
      nome: 'Conta $credencial',
      tipo: tipo,
      email: '$credencial@ecotech.test',
    );
    return atual!;
  }

  @override
  Future<Usuario> registrar({
    required String tipo,
    required String nome,
    required String email,
    required String senha,
    required String senhaConfirmacao,
    String? cpf,
    String? cnpj,
    String? razaoSocial,
  }) async {
    atual = Usuario(id: 'reg-1', nome: nome, tipo: tipo, email: email);
    return atual!;
  }

  @override
  Future<void> logout() async {
    atual = null;
    logouts++;
  }
}

class _FakeFinanceRepository extends FinanceRepository {
  double saldoAtual = 100.0;
  int chamadas = 0;

  @override
  Future<CarteiraData> buscarCarteira() async {
    chamadas++;
    return CarteiraData(
      saldo: saldoAtual,
      pontos: 10,
      pontosPorReal: 100,
      metodos: const [],
      titular: const TitularData(nome: 'Ana', cpf: '123', email: 'a@b.c'),
      saques: const [],
    );
  }
}

class _FakeDashboardRepository extends DashboardRepository {
  _FakeDashboardRepository(this.usuario);

  Usuario usuario;

  @override
  Future<DashboardData> carregar() async => DashboardData(
    tipo: usuario.tipo,
    usuario: usuario,
    metricas: const {
      'saldo': 50.0,
      'pontos': 120,
      'dispositivos': 2,
      'tier': 'Bronze',
    },
    entregas: const [],
    totalEntregasConcluidas: 0,
  );
}

void main() {
  group('Guardas de rota por autenticacao e perfil', () {
    const cidadao = Usuario(id: 'c1', nome: 'Ana', tipo: 'cidadao');
    const empresa = Usuario(id: 'e1', nome: 'Recicla', tipo: 'empresa');
    const admin = Usuario(id: 'a1', nome: 'Admin', tipo: 'administrador');

    test('redireciona usuario sem sessao para /login em rotas protegidas', () {
      const semSessao = AsyncData<Usuario?>(null);
      expect(
        redirecionarRota(location: '/', authState: semSessao),
        '/login',
      );
      expect(
        redirecionarRota(location: '/home', authState: semSessao),
        '/login',
      );
      expect(
        redirecionarRota(location: '/admin/usuarios', authState: semSessao),
        '/login',
      );
      expect(
        redirecionarRota(location: '/login', authState: semSessao),
        isNull,
      );
      expect(
        redirecionarRota(location: '/cadastro', authState: semSessao),
        isNull,
      );
    });

    test('mantem splash e telas de auth durante carregamento e erro', () {
      const carregando = AsyncLoading<Usuario?>();
      final erro = AsyncError<Usuario?>(Exception('offline'), StackTrace.empty);

      expect(redirecionarRota(location: '/', authState: carregando), isNull);
      expect(
        redirecionarRota(location: '/login', authState: carregando),
        isNull,
      );
      expect(
        redirecionarRota(location: '/home', authState: carregando),
        '/',
      );
      expect(redirecionarRota(location: '/', authState: erro), isNull);
      expect(redirecionarRota(location: '/login', authState: erro), isNull);
      expect(redirecionarRota(location: '/home', authState: erro), '/login');
    });

    test('aplica autorizacao por perfil em cada rota do app', () {
      // Cidadao
      expect(rotaPermitidaParaPerfil('/carteira', cidadao.tipo), isTrue);
      expect(rotaPermitidaParaPerfil('/solicitacoes', cidadao.tipo), isTrue);
      expect(
        rotaPermitidaParaPerfil('/solicitacoes/123', cidadao.tipo),
        isTrue,
      );
      expect(
        rotaPermitidaParaPerfil('/solicitacoes/123/agenda', cidadao.tipo),
        isTrue,
      );
      expect(rotaPermitidaParaPerfil('/relatorios', cidadao.tipo), isFalse);
      expect(rotaPermitidaParaPerfil('/planos', cidadao.tipo), isFalse);
      expect(
        rotaPermitidaParaPerfil('/empresa/operacoes', cidadao.tipo),
        isFalse,
      );
      expect(
        rotaPermitidaParaPerfil('/admin/usuarios', cidadao.tipo),
        isFalse,
      );

      // Empresa
      expect(rotaPermitidaParaPerfil('/planos', empresa.tipo), isTrue);
      expect(rotaPermitidaParaPerfil('/relatorios', empresa.tipo), isTrue);
      expect(
        rotaPermitidaParaPerfil('/empresa/operacoes', empresa.tipo),
        isTrue,
      );
      expect(
        rotaPermitidaParaPerfil('/empresa/operacoes/op-1', empresa.tipo),
        isTrue,
      );
      expect(
        rotaPermitidaParaPerfil('/solicitacoes/123/agenda', empresa.tipo),
        isTrue,
      );
      expect(
        rotaPermitidaParaPerfil('/solicitacoes/123', empresa.tipo),
        isFalse,
      );
      expect(rotaPermitidaParaPerfil('/carteira', empresa.tipo), isFalse);
      expect(
        rotaPermitidaParaPerfil('/admin/usuarios', empresa.tipo),
        isFalse,
      );

      // Administrador
      expect(rotaPermitidaParaPerfil('/admin/usuarios', admin.tipo), isTrue);
      expect(rotaPermitidaParaPerfil('/admin/despacho', admin.tipo), isTrue);
      expect(rotaPermitidaParaPerfil('/admin/overrides', admin.tipo), isTrue);
      expect(rotaPermitidaParaPerfil('/admin/precos', admin.tipo), isTrue);
      expect(rotaPermitidaParaPerfil('/relatorios', admin.tipo), isTrue);
      expect(
        rotaPermitidaParaPerfil('/empresa/operacoes', admin.tipo),
        isTrue,
      );
      expect(
        rotaPermitidaParaPerfil('/empresa/operacoes/op-9', admin.tipo),
        isTrue,
      );
      expect(
        rotaPermitidaParaPerfil('/solicitacoes/123/agenda', admin.tipo),
        isTrue,
      );
      expect(rotaPermitidaParaPerfil('/planos', admin.tipo), isFalse);
      expect(
        rotaPermitidaParaPerfil('/empresa/oportunidades', admin.tipo),
        isFalse,
      );
      expect(rotaPermitidaParaPerfil('/carteira', admin.tipo), isFalse);
    });
  });

  group('Interceptador 401 no ApiClient', () {
    test('dispara onUnauthorized e limpa token em rota protegida', () async {
      final storage = _MemoriaTokenStorage()..valor = 'token-antigo';
      var expiracoes = 0;
      final client = ApiClient(
        tokenStorage: storage,
        onUnauthorized: () async {
          expiracoes++;
        },
      );
      client.dio.httpClientAdapter = _StatusAdapter(401);

      await expectLater(
        client.dio.get('/api/v1/dashboard'),
        throwsA(isA<DioException>()),
      );

      expect(storage.valor, isNull);
      expect(storage.limpezas, 1);
      expect(expiracoes, 1);
    });

    test('nao dispara onUnauthorized em 401 de login, cadastro ou /auth/me', () async {
      final storage = _MemoriaTokenStorage()..valor = 'token-atual';
      var expiracoes = 0;
      final client = ApiClient(
        tokenStorage: storage,
        onUnauthorized: () async {
          expiracoes++;
        },
      );
      client.dio.httpClientAdapter = _StatusAdapter(401);

      for (final path in [
        '/api/v1/auth/login',
        '/api/v1/auth/registrar',
        '/api/v1/auth/me',
      ]) {
        await expectLater(
          client.dio.post(path),
          throwsA(isA<DioException>()),
        );
      }

      expect(expiracoes, 0);
      expect(storage.valor, 'token-atual');
    });
  });

  group('Limpeza de cache de providers na sessao', () {
    test('logout e 401 invalidam providers cacheados entre contas', () async {
      final authRepo = _FakeAuthRepository(
        atual: const Usuario(id: 'u1', nome: 'Maria', tipo: 'cidadao'),
      );
      final financeRepo = _FakeFinanceRepository()..saldoAtual = 250.0;
      final container = ProviderContainer(
        overrides: [
          authRepositoryProvider.overrideWithValue(authRepo),
          financeRepositoryProvider.overrideWithValue(financeRepo),
        ],
      );
      addTearDown(container.dispose);

      // Carrega sessao e cache da conta 1.
      final usuarioInicial = await container.read(authControllerProvider.future);
      expect(usuarioInicial?.id, 'u1');

      final carteira1 = await container.read(carteiraProvider.future);
      expect(carteira1.saldo, 250.0);
      expect(financeRepo.chamadas, 1);

      // Logout limpa sessao e invalida cache.
      await container.read(authControllerProvider.notifier).logout();
      expect(container.read(authControllerProvider).valueOrNull, isNull);

      // Conta 2 entra com outro saldo e deve buscar dados novos (sem vazar 250.0).
      financeRepo.saldoAtual = 40.0;
      await container.read(authControllerProvider.notifier).login(
        tipo: 'cidadao',
        credencial: '222',
        senha: '123',
      );
      final carteira2 = await container.read(carteiraProvider.future);
      expect(carteira2.saldo, 40.0);
      expect(financeRepo.chamadas, 2);

      // Evento 401 centralizado expira sessao e invalida cache novamente.
      financeRepo.saldoAtual = 10.0;
      container.read(unauthorizedSignalProvider).add(null);
      await Future<void>.delayed(const Duration(milliseconds: 20));

      expect(container.read(authControllerProvider).valueOrNull, isNull);
      final carteira3 = await container.read(carteiraProvider.future);
      expect(carteira3.saldo, 10.0);
      expect(financeRepo.chamadas, 3);
    });
  });

  group('Protecao de rotas no EcoTechApp', () {
    testWidgets('bloqueia cidadao em /admin/usuarios e redireciona para /home', (
      tester,
    ) async {
      const cidadao = Usuario(id: 'c1', nome: 'Ana', tipo: 'cidadao');
      final authRepo = _FakeAuthRepository(atual: cidadao);
      final dashRepo = _FakeDashboardRepository(cidadao);

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            initialRouteProvider.overrideWithValue('/admin/usuarios'),
            authRepositoryProvider.overrideWithValue(authRepo),
            dashboardRepositoryProvider.overrideWithValue(dashRepo),
            badgesProvider.overrideWith(
              (ref) async => const BadgesData(
                notificacoes: 0,
                mensagens: 0,
                oportunidades: 0,
              ),
            ),
          ],
          child: const EcoTechApp(),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.text('Olá, Ana!'), findsOneWidget);

      // Sinal de 401 deve devolver imediatamente para a tela de login.
      final container = ProviderScope.containerOf(
        tester.element(find.byType(EcoTechApp)),
      );
      container.read(unauthorizedSignalProvider).add(null);
      await tester.pumpAndSettle();

      expect(find.text('Que bom te ver'), findsOneWidget);
      await tester.pumpWidget(const SizedBox());
    });
  });
}
