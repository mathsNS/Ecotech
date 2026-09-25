import 'package:ecotech_mobile/core/theme/app_theme.dart';
import 'package:ecotech_mobile/data/communication/communication_data.dart';
import 'package:ecotech_mobile/data/communication/communication_repository.dart';
import 'package:ecotech_mobile/data/models/usuario.dart';
import 'package:ecotech_mobile/features/auth/auth_controller.dart';
import 'package:ecotech_mobile/features/communication/chat_screen.dart';
import 'package:ecotech_mobile/features/communication/communication_controller.dart';
import 'package:ecotech_mobile/features/communication/conversas_screen.dart';
import 'package:ecotech_mobile/features/company/company_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class _Auth extends AuthController {
  @override
  Future<Usuario?> build() async =>
      const Usuario(id: 'e', nome: 'Recicla Kariri', tipo: 'empresa');
}

const _conversas = [
  ConversaData(
    solicitacaoId: 'abc',
    contatoNome: 'João Silva',
    contatoTipo: 'cidadao',
    estado: 'Solicitado',
    ultimaMensagem: 'Bom dia! Sabe o peso?',
    ultimaMensagemEm: '2026-09-25T11:50:00',
    naoLidas: 1,
    encerrada: false,
  ),
  ConversaData(
    solicitacaoId: 'def',
    contatoNome: 'Ana Beatriz',
    contatoTipo: 'cidadao',
    estado: 'Solicitado',
    ultimaMensagem: 'Até amanhã!',
    ultimaMensagemEm: '2026-09-25T11:51:00',
    naoLidas: 0,
    encerrada: false,
  ),
];

class _Repository extends CommunicationRepository {
  final List<String> enviadas = [];
  @override
  Future<MensagensPaginaData> listarMensagens(
    String solicitacaoId, {
    int pagina = 1,
  }) async => const MensagensPaginaData(
    mensagens: [
      MensagemData(
        id: '1',
        tipo: 'MENSAGEM',
        texto: 'Podem coletar amanhã?',
        criadoEm: '2026-09-25T11:50:00',
        propria: false,
        remetenteNome: 'João Silva',
        remetenteTipo: 'cidadao',
      ),
    ],
    pagina: 1,
    temMais: false,
    cidadao: 'João Silva',
    estado: 'Solicitado',
    localizacao: 'Recicla Kariri - Centro de Triagem',
  );
  @override
  Future<void> marcarConversaLida(String solicitacaoId) async {}
  @override
  Future<MensagemData> enviarMensagem(
    String solicitacaoId,
    String texto,
    String idCliente,
  ) async {
    enviadas.add(texto);
    return MensagemData(
      id: '2',
      tipo: 'MENSAGEM',
      texto: texto,
      criadoEm: '2026-09-25T11:52:00',
      propria: true,
      remetenteNome: 'Recicla Kariri',
      remetenteTipo: 'empresa',
    );
  }
}

Future<void> _mount(
  WidgetTester tester,
  Widget screen,
  _Repository repo,
) async {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.resetPhysicalSize);
  addTearDown(tester.view.resetDevicePixelRatio);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        authControllerProvider.overrideWith(_Auth.new),
        communicationRepositoryProvider.overrideWithValue(repo),
        conversasProvider.overrideWith((ref) async => _conversas),
        oportunidadesEmpresaProvider.overrideWith((ref) async => const []),
        badgesProvider.overrideWith(
          (ref) async =>
              const BadgesData(notificacoes: 4, mensagens: 1, oportunidades: 0),
        ),
      ],
      child: MaterialApp(theme: AppTheme.light(), home: screen),
    ),
  );
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('central filtra nome e coleta sem perder contagem de não lidas', (
    tester,
  ) async {
    await _mount(tester, const ConversasScreen(), _Repository());
    expect(find.text('João Silva'), findsOneWidget);
    expect(find.text('Ana Beatriz'), findsOneWidget);
    await tester.enterText(find.byType(TextField), 'ANA');
    await tester.pumpAndSettle();
    expect(find.text('João Silva'), findsNothing);
    expect(find.text('Ana Beatriz'), findsOneWidget);
    expect(
      find.text('Canal privado por coleta. 1 mensagem não lida.'),
      findsOneWidget,
    );
    await tester.enterText(find.byType(TextField), 'abc');
    await tester.pumpAndSettle();
    expect(find.text('João Silva'), findsOneWidget);
    await tester.enterText(find.byType(TextField), 'inexistente');
    await tester.pumpAndSettle();
    expect(
      find.text('Nenhuma conversa encontrada para esta busca.'),
      findsOneWidget,
    );
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });

  testWidgets('chat mantém contexto, bloqueia envio vazio e envia mensagem', (
    tester,
  ) async {
    final repo = _Repository();
    await _mount(tester, const ChatScreen(solicitacaoId: 'abc'), repo);
    expect(find.text('Coleta #abc'), findsOneWidget);
    expect(find.text('Recicla Kariri - Centro de Triagem'), findsOneWidget);
    expect(find.byTooltip('Agenda'), findsOneWidget);
    expect(
      tester
          .widget<IconButton>(
            find.byWidgetPredicate(
              (widget) => widget is IconButton && widget.tooltip == 'Enviar',
            ),
          )
          .onPressed,
      isNull,
    );
    await tester.enterText(find.byType(TextField), 'Combinado, até amanhã!');
    await tester.pump();
    await tester.tap(find.byTooltip('Enviar'));
    await tester.pumpAndSettle();
    expect(repo.enviadas, ['Combinado, até amanhã!']);
    expect(find.text('Combinado, até amanhã!'), findsOneWidget);
    expect(
      tester
          .widget<IconButton>(
            find.byWidgetPredicate(
              (widget) => widget is IconButton && widget.tooltip == 'Enviar',
            ),
          )
          .onPressed,
      isNull,
    );
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
  });
}
