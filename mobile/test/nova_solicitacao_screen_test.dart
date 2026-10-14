import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/core/api/api_exception.dart';
import 'package:ecotech_mobile/features/citizen/nova_solicitacao_screen.dart';
import 'package:ecotech_mobile/features/citizen/widgets/collection_fields.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import 'dart:async';

import 'package:ecotech_mobile/data/citizen/citizen_data.dart';
import 'package:ecotech_mobile/data/citizen/citizen_repository.dart';
import 'package:ecotech_mobile/features/citizen/citizen_controller.dart';

class CollectionRepository extends CitizenRepository {
  final address = Completer<EnderecoCepData>();
  final points = Completer<List<PontoColetaData>>();
  @override
  Future<List<PontoColetaData>> listarPontos() => points.future;
  final submission = Completer<SolicitacaoDetalhesData>();
  final requests = <NovaSolicitacaoData>[];
  @override
  Future<SolicitacaoDetalhesData> criarSolicitacao(NovaSolicitacaoData data) {
    requests.add(data);
    return submission.future;
  }

  @override
  Future<EnderecoCepData> consultarCep(String cep) => address.future;
}

Future<void> pumpCollection(
  WidgetTester tester, {
  double scale = 1,
  Size size = const Size(390, 844),
  bool atPoint = false,
  CollectionRepository? repository,
}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  final router = GoRouter(
    initialLocation: '/nova',
    routes: [
      GoRoute(
        path: '/nova',
        builder: (_, _) => NovaSolicitacaoScreen(
          tipoInicial: atPoint ? 'entrega_ponto' : 'domiciliar',
          pontoIdInicial: atPoint ? 'ponto-1' : null,
        ),
      ),
      GoRoute(
        path: '/solicitacoes/:id',
        builder: (_, state) =>
            Scaffold(body: Text('Solicitação ${state.pathParameters['id']}')),
      ),
      GoRoute(
        path: '/home',
        builder: (_, _) => const Scaffold(body: Text('Início')),
      ),
    ],
  );
  addTearDown(router.dispose);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        if (repository != null)
          citizenRepositoryProvider.overrideWithValue(repository),
      ],
      child: MaterialApp.router(
        theme: AppTheme.light(),
        routerConfig: router,
        builder: (context, child) => MediaQuery(
          data: MediaQuery.of(context)
              .copyWith(textScaler: TextScaler.linear(scale)),
          child: child!,
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

Finder field(String label) => find.descendant(
  of: find.byWidgetPredicate(
    (widget) => widget is CollectionField && widget.label == label,
  ),
  matching: find.byType(TextField),
);

Future<void> tapVisible(WidgetTester tester, Finder finder) async {
  if (finder.evaluate().isEmpty) {
    await tester.scrollUntilVisible(
      finder,
      300,
      scrollable: find.byType(Scrollable).first,
    );
  }
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

Future<void> fillAddress(WidgetTester tester) async {
  await tester.enterText(field('Modelo ou nome'), 'Celular');
  await tester.enterText(field('Quantidade'), '3');
  await tapVisible(tester, find.text('Próximo'));
  for (final entry in {
    'CEP': '63000000',
    'Número': '12',
    'Endereço': 'Rua Um',
    'Bairro': 'Centro',
    'Cidade': 'Crato',
    'UF': 'ce',
    'Nome para contato': 'Maria',
  }.entries) {
    await tester.enterText(field(entry.key), entry.value);
  }
  await tapVisible(tester, find.text('Próximo'));
}

Future<void> chooseSchedule(WidgetTester tester) async {
  await tapVisible(tester, find.text('Selecione uma data'));
  await tapVisible(tester, find.text('OK'));
  await tapVisible(tester, find.text('Disponível a partir de'));
  await tapVisible(tester, find.text('OK'));
  await tapVisible(tester, find.text('Disponível até'));
  await tapVisible(tester, find.text('OK'));
}

void main() {
  testWidgets('entrega no ponto aguarda um ponto válido antes de avançar', (
    tester,
  ) async {
    final repository = CollectionRepository();
    await pumpCollection(tester, repository: repository, atPoint: true);
    await tester.enterText(field('Modelo ou nome'), 'Celular');
    await tester.tap(find.text('Próximo'));
    await tester.pump();
    await tester.enterText(field('Nome para contato'), 'Maria');
    await tester.tap(find.text('Próximo'));
    await tester.pump();
    expect(find.text('Etapa 2 de 3 · Ponto de coleta'), findsOneWidget);
    repository.points.complete([
      PontoColetaData.fromJson({'id': 'ponto-1', 'nome': 'Ponto Central'}),
    ]);
    await tester.pumpAndSettle();
    await tapVisible(tester, find.text('Próximo'));
    expect(find.text('Etapa 3 de 3 · Agendamento'), findsOneWidget);
    await chooseSchedule(tester);
    await tester.tap(find.text('Criar solicitação'));
    await tester.pump();
    expect(repository.requests.single.campos['ponto_id'], 'ponto-1');
    expect(repository.requests.single.campos.containsKey('cep'), isFalse);
    repository.submission.complete(
      SolicitacaoDetalhesData.fromJson({'id': 'entrega-1'}),
    );
    await tester.pumpAndSettle();
    expect(find.text('Solicitação entrega-1'), findsOneWidget);
  });

  testWidgets('retorno do sistema volta uma etapa sem descartar o formulário', (
    tester,
  ) async {
    await pumpCollection(tester);
    await tester.enterText(field('Modelo ou nome'), 'Celular');
    await tapVisible(tester, find.text('Próximo'));
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    expect(find.text('Etapa 1 de 3 · Dispositivo'), findsOneWidget);
    expect(find.text('Celular'), findsOneWidget);
  });

  testWidgets('etapas cabem em 320 px com fonte ampliada e teclado', (
    tester,
  ) async {
    await pumpCollection(tester, scale: 2, size: const Size(320, 800));
    await fillAddress(tester);
    expect(tester.takeException(), isNull);
    await tapVisible(tester, find.text('Anterior'));
    tester.view.viewInsets = const FakeViewPadding(bottom: 250);
    addTearDown(tester.view.resetViewInsets);
    await tester.pumpAndSettle();
    await tester.ensureVisible(field('Nome para contato'));
    await tester.pumpAndSettle();
    expect(find.text('Próximo').hitTestable(), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets(
    'envia uma única solicitação com os dados e abre o detalhe real',
    (tester) async {
      final repository = CollectionRepository();
      await pumpCollection(tester, repository: repository);
      await fillAddress(tester);
      await tapVisible(tester, find.text('Criar solicitação'));
      expect(repository.requests, isEmpty);
      expect(
        find.text('Selecione a data e a janela de horário.'),
        findsOneWidget,
      );
      await chooseSchedule(tester);
      await tester.tap(find.text('Criar solicitação'));
      await tester.tap(find.text('Criar solicitação'));
      await tester.pump();
      expect(repository.requests, hasLength(1));
      final data = repository.requests.single.campos;
      expect(data['quantidade'], 3);
      expect(data['logradouro'], 'Rua Um');
      expect(data['nome_contato'], 'Maria');
      expect(data['uf'], 'CE');
      expect(data['peso_kg'], '');
      expect(data['horario_inicio'], '09:00');
      expect(data['horario_fim'], '11:00');
      repository.submission.complete(
        SolicitacaoDetalhesData.fromJson({'id': 'nova-123'}),
      );
      await tester.pumpAndSettle();
      expect(find.text('Solicitação nova-123'), findsOneWidget);
    },
  );

  testWidgets('falha no envio mantém a revisão e libera nova tentativa', (
    tester,
  ) async {
    final repository = CollectionRepository();
    await pumpCollection(tester, repository: repository);
    await fillAddress(tester);
    await chooseSchedule(tester);
    await tester.tap(find.text('Criar solicitação'));
    await tester.pump();
    repository.submission.completeError(ApiException('Serviço indisponível.'));
    await tester.pumpAndSettle();
    expect(find.text('Serviço indisponível.'), findsOneWidget);
    expect(find.text('3x Celular'), findsOneWidget);
    expect(
      tester
          .widget<ElevatedButton>(
            find.widgetWithText(ElevatedButton, 'Criar solicitação'),
          )
          .onPressed,
      isNotNull,
    );
  });

  testWidgets('consulta CEP sem substituir um CEP editado durante a busca', (
    tester,
  ) async {
    final repository = CollectionRepository();
    await pumpCollection(tester, repository: repository);
    await tester.enterText(field('Modelo ou nome'), 'Celular');
    await tapVisible(tester, find.text('Próximo'));
    await tester.enterText(field('CEP'), '63000000');
    await tester.ensureVisible(find.byTooltip('Buscar CEP'));
    await tester.tap(find.byTooltip('Buscar CEP'));
    await tester.pump();
    await tester.enterText(field('CEP'), '63100000');
    repository.address.complete(
      const EnderecoCepData(
        cep: '63000000',
        logradouro: 'Rua antiga',
        bairro: 'Centro',
        cidade: 'Crato',
        uf: 'CE',
      ),
    );
    await tester.pumpAndSettle();
    expect(
      tester.widget<TextField>(field('Endereço')).controller!.text,
      isEmpty,
    );
    await tapVisible(tester, find.text('Próximo'));
    expect(find.text('Campo obrigatório.'), findsWidgets);
    expect(find.text('Etapa 2 de 3 · Endereço'), findsOneWidget);
  });

  testWidgets('endereço manual e contato permanecem ao voltar', (tester) async {
    await pumpCollection(tester);
    await tester.enterText(field('Modelo ou nome'), 'Celular');
    await tapVisible(tester, find.text('Próximo'));
    for (final entry in {
      'CEP': '63000000',
      'Número': '12',
      'Endereço': 'Rua Um',
      'Bairro': 'Centro',
      'Cidade': 'Crato',
      'UF': 'CE',
      'Nome para contato': 'Maria',
    }.entries) {
      await tester.enterText(field(entry.key), entry.value);
    }
    await tapVisible(tester, find.text('Próximo'));
    expect(find.text('Etapa 3 de 3 · Agendamento'), findsOneWidget);
    await tapVisible(tester, find.text('Anterior'));
    expect(
      tester.widget<TextField>(field('Endereço')).controller!.text,
      'Rua Um',
    );
    expect(
      tester.widget<TextField>(field('Nome para contato')).controller!.text,
      'Maria',
    );
  });

  testWidgets('quantidade e categoria acompanham a edição e o retorno', (
    tester,
  ) async {
    await pumpCollection(tester);
    await tester.enterText(field('Modelo ou nome'), 'Notebook de teste');
    await tester.enterText(field('Quantidade'), '3');
    await tapVisible(
      tester,
      find.byType(DropdownButtonFormField<String>).first,
    );
    await tapVisible(tester, find.text('Computador').last);
    expect(find.text('Notebook'), findsOneWidget);
    await tapVisible(tester, find.text('Próximo'));
    await tapVisible(tester, find.text('Anterior'));
    expect(tester.widget<TextField>(field('Quantidade')).controller!.text, '3');
    expect(find.text('Notebook'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('ações ficam acessíveis e voltar retorna à etapa anterior', (
    tester,
  ) async {
    await pumpCollection(tester);
    expect(find.text('Próximo').hitTestable(), findsOneWidget);
    await tester.enterText(field('Modelo ou nome'), 'Celular de teste');
    await tapVisible(tester, find.text('Próximo'));
    expect(find.text('Etapa 2 de 3 · Endereço'), findsOneWidget);
    await tapVisible(tester, find.byTooltip('Voltar'));
    expect(find.text('Etapa 1 de 3 · Dispositivo'), findsOneWidget);
    expect(find.text('Celular de teste'), findsOneWidget);
    await tapVisible(tester, find.text('Cancelar'));
    expect(find.text('Início'), findsOneWidget);
  });

  testWidgets('apresenta a etapa e mantém a validação do dispositivo', (
    tester,
  ) async {
    await pumpCollection(tester);
    expect(find.text('COLETA DOMICILIAR'), findsOneWidget);
    expect(find.text('Etapa 1 de 3 · Dispositivo'), findsOneWidget);
    await tapVisible(tester, find.text('Próximo'));
    expect(find.text('Campo obrigatório.'), findsOneWidget);
    expect(field('Modelo ou nome'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
