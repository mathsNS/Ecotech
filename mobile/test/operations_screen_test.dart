import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/data/citizen/citizen_data.dart';
import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/data/company/operation_data.dart';
import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:ecotech_mobile/features/auth/auth_controller.dart';
import 'package:ecotech_mobile/features/citizen/citizen_controller.dart';
import 'package:ecotech_mobile/features/citizen/solicitacoes_screen.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:ecotech_mobile/features/company/company_controller.dart';
import 'package:ecotech_mobile/features/company/operacoes_empresa_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _CompanyAuthController extends AuthController {
  @override
  Future<Usuario?> build() async =>
      const Usuario(id: 'empresa-1', nome: 'Recicla Kariri', tipo: 'empresa');
}

class _CitizenAuthController extends AuthController {
  @override
  Future<Usuario?> build() async =>
      const Usuario(id: 'cidadao-1', nome: 'João Silva', tipo: 'cidadao');
}

const _stats = {
  'pendentes': 4,
  'em_coleta': 4,
  'processando': 2,
  'finalizadas': 5,
};

void main() {
  testWidgets('empresa visualiza gerenciamento no layout de referencia', (
    tester,
  ) async {
    final operation = OperacaoResumoData(
      id: 'df30af12-abcd',
      cidadao: 'João Silva',
      estado: 'Reciclado',
      pesoKg: 2.4,
      pesoEstimadoKg: 2.4,
      pesoOrigem: 'aferido',
      quantidadeItens: 1,
      dataCriacao: DateTime(2026, 8, 31),
      pontoColeta: 'Recicla Kariri - Centro de Triagem',
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_CompanyAuthController.new),
          operacoesEmpresaProvider.overrideWith(
            (ref, query) async => OperacoesPaginaData(
              operacoes: [operation],
              estatisticas: _stats,
              pagina: 1,
              totalPaginas: 1,
              total: 15,
            ),
          ),
          oportunidadesEmpresaProvider.overrideWith((ref) async => const []),
          badgesProvider.overrideWith(
            (ref) async => const BadgesData(
              notificacoes: 4,
              mensagens: 0,
              oportunidades: 0,
            ),
          ),
        ],
        child: MaterialApp(
          theme: AppTheme.light(),
          home: const OperacoesEmpresaScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Gerenciamento de\nOperações'), findsOneWidget);
    expect(find.text('Solicitações Pendentes'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('15 encontradas'),
      350,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('15 encontradas'), findsOneWidget);
    expect(find.text('João Silva'), findsOneWidget);
    expect(find.text('Ver Detalhes'), findsOneWidget);
    expect(find.bySemanticsLabel('Abrir agenda'), findsOneWidget);
    expect(find.bySemanticsLabel('Abrir conversa'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('cidadão recebe a mesma linguagem visual nas operações', (
    tester,
  ) async {
    final request = SolicitacaoData(
      id: '8ed47b81-abcd',
      estado: 'Em Processamento',
      pesoEstimadoKg: 5.4,
      pesoConfirmadoKg: null,
      pesoOrigem: 'estimado',
      quantidadeItens: 1,
      empresa: 'TechLixo Soluções',
      dataCriacao: DateTime(2026, 8, 31),
    );
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authControllerProvider.overrideWith(_CitizenAuthController.new),
          solicitacoesProvider.overrideWith(
            (ref, state) async => SolicitacoesPagina(
              itens: [request],
              pagina: 1,
              totalPaginas: 1,
              total: 1,
              estatisticas: _stats,
            ),
          ),
          badgesProvider.overrideWith(
            (ref) async => const BadgesData(
              notificacoes: 2,
              mensagens: 1,
              oportunidades: 0,
            ),
          ),
        ],
        child: MaterialApp(
          theme: AppTheme.light(),
          home: const SolicitacoesScreen(),
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Minhas\nOperações'), findsOneWidget);
    expect(find.text('Em Processamento'), findsOneWidget);
    expect(find.text('Nova solicitação'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Solicitação #8ed47b81'),
      350,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Solicitação #8ed47b81'), findsOneWidget);
    expect(find.text('TechLixo Soluções'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
  });
}
