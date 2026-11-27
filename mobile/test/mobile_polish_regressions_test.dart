import 'dart:typed_data';

import 'package:ecotech_mobile/data/citizen/citizen_data.dart';
import 'package:ecotech_mobile/data/citizen/citizen_repository.dart';
import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/data/company/operation_data.dart';
import 'package:ecotech_mobile/data/company/operation_repository.dart';
import 'package:ecotech_mobile/features/citizen/citizen_controller.dart';
import 'package:ecotech_mobile/features/citizen/solicitacao_detalhes_screen.dart';
import 'package:ecotech_mobile/features/communication/agenda_screen.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:ecotech_mobile/features/company/company_controller.dart';
import 'package:ecotech_mobile/features/company/operacao_detalhes_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _FotoErroCitizenRepo extends CitizenRepository {
  @override
  Future<Uint8List> baixarFoto(String url) =>
      Future<Uint8List>.error(Exception('404'));
}

class _FotoErroOperationRepo extends OperationRepository {
  @override
  Future<Uint8List> baixarFoto(String url) =>
      Future<Uint8List>.error(Exception('404'));
}

void main() {
  test('rotuloEventoAgenda traduz eventos reais do backend', () {
    expect(rotuloEventoAgenda('ACEITA'), 'Horário aceito');
    expect(rotuloEventoAgenda('REJEITADA'), 'Proposta recusada');
    expect(rotuloEventoAgenda('JANELA_SOLICITADA'), 'Janela solicitada');
    expect(rotuloEventoAgenda('PROPOSTA'), 'Novo horário proposto');
    expect(rotuloEventoAgenda('ACEITE'), 'Horário aceito');
    expect(rotuloEventoAgenda('RECUSA'), 'Proposta recusada');
    expect(rotuloEventoAgenda('CRIACAO'), 'Agenda criada');
  });

  testWidgets('foto com erro em SolicitacaoDetalhesScreen exibe fallback sem loop', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          citizenRepositoryProvider.overrideWithValue(_FotoErroCitizenRepo()),
          solicitacaoDetalhesProvider.overrideWith(
            (ref, id) async => SolicitacaoDetalhesData.fromJson({
              'id': id,
              'estado': 'Solicitado',
              'peso_estimado_kg': 2.0,
              'itens': const [],
              'fotos': [
                {'id': 'f1', 'url': '/api/v1/solicitacoes/$id/fotos/f1'},
              ],
            }),
          ),
          badgesProvider.overrideWith(
            (ref) async => const BadgesData(
              notificacoes: 0,
              mensagens: 0,
              oportunidades: 0,
            ),
          ),
        ],
        child: const MaterialApp(
          home: SolicitacaoDetalhesScreen(id: 'sol-12345678'),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Foto indisponível'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('OperacaoDetalhesScreen exibe acentuacao correta e fallback de foto', (
    tester,
  ) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          operationRepositoryProvider.overrideWithValue(
            _FotoErroOperationRepo(),
          ),
          operacaoDetalhesProvider.overrideWith(
            (ref, id) async => OperacaoDetalhesData.fromJson({
              'id': id,
              'cidadao': 'Ana Paula',
              'estado': 'Em Processamento',
              'peso_estimado_kg': 2.0,
              'itens': const [],
              'fotos': [
                {'id': 'f1', 'url': '/api/v1/operacoes/$id/fotos/f1'},
              ],
            }),
          ),
          badgesProvider.overrideWith(
            (ref) async => const BadgesData(
              notificacoes: 0,
              mensagens: 0,
              oportunidades: 0,
            ),
          ),
        ],
        child: const MaterialApp(
          home: OperacaoDetalhesScreen(id: 'op-12345678'),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Operação #op-12345'), findsOneWidget);
    expect(find.text('Conferência de peso'), findsOneWidget);
    expect(find.text('Diferença'), findsOneWidget);
    expect(find.text('Foto indisponível'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    await tester.pumpWidget(const SizedBox());
  });
}
