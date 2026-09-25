import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/communication/communication_data.dart';
import '../../shared/widgets/app_back_button.dart';
import '../auth/auth_controller.dart';
import '../operations/operations_widgets.dart';
import 'communication_controller.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({required this.solicitacaoId, super.key});

  final String solicitacaoId;

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _texto = TextEditingController();
  final _scroll = ScrollController();
  final List<MensagemData> _mensagens = [];
  Timer? _timer;
  bool _carregando = true;
  bool _maisAntigas = false;
  bool _enviando = false;
  bool _temMais = false;
  int _pagina = 1;
  String _cidadao = '';
  String _estado = '';
  String _localizacao = '';
  String? _erro;

  @override
  void initState() {
    super.initState();
    _carregar(inicial: true);
    _timer = Timer.periodic(const Duration(seconds: 20), (_) => _atualizar());
  }

  @override
  void dispose() {
    _timer?.cancel();
    _texto.dispose();
    _scroll.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final usuario = ref.watch(authControllerProvider).valueOrNull;
    var contato = usuario?.tipo == 'empresa' ? _cidadao : '';
    for (final conversa
        in ref.watch(conversasProvider).valueOrNull ?? <ConversaData>[]) {
      if (conversa.solicitacaoId == widget.solicitacaoId) {
        contato = conversa.contatoNome;
      }
    }
    final id = widget.solicitacaoId.length > 8
        ? widget.solicitacaoId.substring(0, 8)
        : widget.solicitacaoId;
    return Scaffold(
      backgroundColor: operationsBackground,
      appBar: AppBar(
        backgroundColor: const Color(0xFFF2F6F3),
        shape: const Border(bottom: BorderSide(color: operationsBorder)),
        leading: const AppBackButton(fallbackRoute: '/conversas'),
        leadingWidth: 48,
        titleSpacing: 0,
        title: Row(
          children: [
            CircleAvatar(
              radius: 19,
              backgroundColor: operationsSoftGreen,
              foregroundColor: operationsDeepGreen,
              child: Text(
                contato.trim().isEmpty
                    ? 'E'
                    : contato.trim().substring(0, 1).toUpperCase(),
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    contato.isEmpty ? 'Conversa da coleta' : contato,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    'Coleta #$id',
                    style: const TextStyle(
                      fontSize: 11,
                      color: operationsMuted,
                      letterSpacing: .5,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          IconButton.filledTonal(
            tooltip: 'Agenda',
            style: IconButton.styleFrom(
              backgroundColor: operationsSoftGreen,
              foregroundColor: operationsDeepGreen,
            ),
            onPressed: () =>
                context.push('/solicitacoes/${widget.solicitacaoId}/agenda'),
            icon: const Icon(Icons.calendar_month_outlined, size: 20),
          ),
          const SizedBox(width: 12),
        ],
      ),
      body: Column(
        children: [
          _ContextoConversa(
            solicitacaoId: widget.solicitacaoId,
            localizacao: _localizacao,
            estado: _estado,
            tipoUsuario: usuario?.tipo,
          ),
          Expanded(child: _corpo()),
          _CampoMensagem(
            controller: _texto,
            enviando: _enviando,
            onEnviar: _enviar,
          ),
        ],
      ),
    );
  }

  Widget _corpo() {
    if (_carregando) return const Center(child: CircularProgressIndicator());
    if (_erro != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off_outlined, size: 42),
              const SizedBox(height: 10),
              Text(_erro!, textAlign: TextAlign.center),
              TextButton(
                onPressed: () => _carregar(inicial: true),
                child: const Text('Tentar novamente'),
              ),
            ],
          ),
        ),
      );
    }
    if (_mensagens.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'A conversa está pronta. Envie a primeira mensagem sobre esta coleta.',
            textAlign: TextAlign.center,
          ),
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _atualizar,
      child: ListView.builder(
        controller: _scroll,
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 18),
        itemCount: _mensagens.length + (_temMais ? 1 : 0),
        itemBuilder: (context, index) {
          if (_temMais && index == 0) {
            return Center(
              child: TextButton.icon(
                onPressed: _maisAntigas ? null : _carregarMais,
                icon: _maisAntigas
                    ? const SizedBox.square(
                        dimension: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.expand_less),
                label: const Text('Carregar mensagens anteriores'),
              ),
            );
          }
          final itemIndex = index - (_temMais ? 1 : 0);
          return _mensagens[itemIndex].evento
              ? _EventoSistema(_mensagens[itemIndex])
              : _BolhaMensagem(_mensagens[itemIndex]);
        },
      ),
    );
  }

  Future<void> _carregar({required bool inicial}) async {
    if (inicial && mounted) {
      setState(() {
        _carregando = true;
        _erro = null;
      });
    }
    try {
      final pagina = await ref
          .read(communicationRepositoryProvider)
          .listarMensagens(widget.solicitacaoId);
      if (!mounted) return;
      setState(() {
        _mensagens
          ..clear()
          ..addAll(pagina.mensagens);
        _pagina = 1;
        _temMais = pagina.temMais;
        _cidadao = pagina.cidadao;
        _estado = pagina.estado;
        _localizacao = pagina.localizacao;
        _carregando = false;
      });
      await _marcarLida();
      WidgetsBinding.instance.addPostFrameCallback((_) => _irAoFim());
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _carregando = false;
        _erro = _mensagemErro(error);
      });
    }
  }

  Future<void> _atualizar() async {
    if (_carregando || _enviando || !mounted) return;
    try {
      final pagina = await ref
          .read(communicationRepositoryProvider)
          .listarMensagens(widget.solicitacaoId);
      if (!mounted) return;
      final existentes = _mensagens.map((item) => item.id).toSet();
      final novas = pagina.mensagens
          .where((item) => !existentes.contains(item.id))
          .toList();
      setState(() {
        _mensagens.addAll(novas);
        _cidadao = pagina.cidadao;
        _estado = pagina.estado;
        _localizacao = pagina.localizacao;
      });
      if (novas.isNotEmpty) _irAoFim();
      await _marcarLida();
    } catch (_) {
      // A atualização silenciosa tenta novamente no próximo ciclo.
    }
  }

  Future<void> _carregarMais() async {
    setState(() => _maisAntigas = true);
    try {
      final pagina = await ref
          .read(communicationRepositoryProvider)
          .listarMensagens(widget.solicitacaoId, pagina: _pagina + 1);
      if (!mounted) return;
      final existentes = _mensagens.map((item) => item.id).toSet();
      setState(() {
        _mensagens.insertAll(
          0,
          pagina.mensagens.where((item) => !existentes.contains(item.id)),
        );
        _pagina = pagina.pagina;
        _temMais = pagina.temMais;
      });
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_mensagemErro(error))));
      }
    } finally {
      if (mounted) setState(() => _maisAntigas = false);
    }
  }

  Future<void> _enviar() async {
    final mensagem = _texto.text.trim();
    if (mensagem.isEmpty || _enviando) return;
    setState(() => _enviando = true);
    try {
      final enviada = await ref
          .read(communicationRepositoryProvider)
          .enviarMensagem(
            widget.solicitacaoId,
            mensagem,
            'mobile-${DateTime.now().microsecondsSinceEpoch}',
          );
      if (!mounted) return;
      if (!_mensagens.any((item) => item.id == enviada.id)) {
        setState(() => _mensagens.add(enviada));
      }
      _texto.clear();
      ref.invalidate(conversasProvider);
      _irAoFim();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_mensagemErro(error))));
      }
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  Future<void> _marcarLida() async {
    await ref
        .read(communicationRepositoryProvider)
        .marcarConversaLida(widget.solicitacaoId);
    ref.invalidate(badgesProvider);
    ref.invalidate(conversasProvider);
  }

  void _irAoFim() {
    if (!_scroll.hasClients) return;
    _scroll.animateTo(
      _scroll.position.maxScrollExtent,
      duration: const Duration(milliseconds: 250),
      curve: Curves.easeOut,
    );
  }

  String _mensagemErro(Object error) => error is ApiException
      ? error.mensagem
      : 'Não foi possível carregar a conversa.';
}

class _ContextoConversa extends StatelessWidget {
  const _ContextoConversa({
    required this.solicitacaoId,
    required this.localizacao,
    required this.estado,
    required this.tipoUsuario,
  });

  final String solicitacaoId;
  final String localizacao;
  final String estado;
  final String? tipoUsuario;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Container(
        width: double.infinity,
        color: const Color(0xFFECF6F0),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
        child: const Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.lock_outline, size: 13, color: operationsDeepGreen),
            SizedBox(width: 6),
            Flexible(
              child: Text(
                'Canal privado entre cidadão e empresa responsável.',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 11, color: operationsDeepGreen),
              ),
            ),
          ],
        ),
      ),
      TextButton.icon(
        onPressed: () => context.push(
          tipoUsuario == 'empresa' || tipoUsuario == 'administrador'
              ? '/empresa/operacoes/$solicitacaoId'
              : '/solicitacoes/$solicitacaoId',
        ),
        style: TextButton.styleFrom(foregroundColor: operationsMuted),
        icon: Icon(
          localizacao.isEmpty ? Icons.info_outline : Icons.location_on_outlined,
          size: 14,
        ),
        label: Text(
          localizacao.isNotEmpty
              ? localizacao
              : estado.isEmpty
              ? 'Detalhes da coleta'
              : estado.replaceAll('_', ' '),
          style: const TextStyle(fontSize: 11),
        ),
      ),
    ],
  );
}

class _BolhaMensagem extends StatelessWidget {
  const _BolhaMensagem(this.mensagem);

  final MensagemData mensagem;

  @override
  Widget build(BuildContext context) => Align(
    alignment: mensagem.propria ? Alignment.centerRight : Alignment.centerLeft,
    child: Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.sizeOf(context).width * 0.78,
      ),
      margin: const EdgeInsets.symmetric(vertical: 4),
      padding: const EdgeInsets.fromLTRB(14, 11, 14, 10),
      decoration: BoxDecoration(
        color: mensagem.propria ? const Color(0xFF205C3D) : Colors.white,
        boxShadow: const [
          BoxShadow(
            color: Color(0x14000000),
            blurRadius: 2,
            offset: Offset(0, 2),
          ),
        ],
        borderRadius: BorderRadius.only(
          topLeft: const Radius.circular(22),
          topRight: const Radius.circular(22),
          bottomLeft: Radius.circular(mensagem.propria ? 22 : 12),
          bottomRight: Radius.circular(mensagem.propria ? 12 : 22),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '${mensagem.remetenteNome} · ${_tipo(mensagem.remetenteTipo)}',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w700,
              color: mensagem.propria ? Colors.white70 : operationsMuted,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            mensagem.texto,
            style: TextStyle(
              fontSize: 14,
              height: 1.6,
              color: mensagem.propria ? Colors.white : operationsDark,
            ),
          ),
          const SizedBox(height: 4),
          Align(
            alignment: Alignment.centerRight,
            child: Text(
              AppFormatters.dataHoraTexto(mensagem.criadoEm),
              style: TextStyle(
                fontSize: 10,
                color: mensagem.propria ? Colors.white70 : AppColors.textLight,
              ),
            ),
          ),
        ],
      ),
    ),
  );

  static String _tipo(String tipo) => switch (tipo) {
    'cidadao' => 'Cidadão',
    'empresa' => 'Empresa',
    _ => 'Sistema',
  };
}

class _EventoSistema extends StatelessWidget {
  const _EventoSistema(this.mensagem);

  final MensagemData mensagem;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 9, horizontal: 20),
    child: Row(
      children: [
        const Expanded(child: Divider()),
        Flexible(
          flex: 4,
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: Column(
              children: [
                const Icon(
                  Icons.info_outline,
                  size: 18,
                  color: AppColors.textLight,
                ),
                const SizedBox(height: 3),
                Text(
                  mensagem.texto,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 12),
                ),
                Text(
                  AppFormatters.dataHoraTexto(mensagem.criadoEm),
                  style: const TextStyle(
                    fontSize: 10,
                    color: AppColors.textLight,
                  ),
                ),
              ],
            ),
          ),
        ),
        const Expanded(child: Divider()),
      ],
    ),
  );
}

class _CampoMensagem extends StatelessWidget {
  const _CampoMensagem({
    required this.controller,
    required this.enviando,
    required this.onEnviar,
  });

  final TextEditingController controller;
  final bool enviando;
  final VoidCallback onEnviar;

  @override
  Widget build(BuildContext context) => SafeArea(
    top: false,
    child: Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: Color(0xFFE1E5E3))),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              enabled: !enviando,
              maxLength: 2000,
              minLines: 1,
              maxLines: 5,
              textCapitalization: TextCapitalization.sentences,
              decoration: InputDecoration(
                hintText: 'Escreva uma mensagem...',
                hintStyle: const TextStyle(
                  fontSize: 13,
                  color: operationsMuted,
                ),
                counterText: '',
                fillColor: const Color(0xFFEDF7F1),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 14,
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(28),
                  borderSide: const BorderSide(color: Color(0xFFBDD5C7)),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(28),
                  borderSide: const BorderSide(
                    color: Color(0xFFBDD5C7),
                    width: 1.5,
                  ),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(28),
                  borderSide: const BorderSide(
                    color: AppColors.primary,
                    width: 1.5,
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(width: 7),
          ValueListenableBuilder<TextEditingValue>(
            valueListenable: controller,
            builder: (context, value, _) => IconButton.filled(
              tooltip: 'Enviar',
              style: IconButton.styleFrom(
                backgroundColor: operationsDeepGreen,
                disabledBackgroundColor: const Color(0xFFA3BDAE),
                disabledForegroundColor: Colors.white,
                minimumSize: const Size(46, 46),
              ),
              onPressed: enviando || value.text.trim().isEmpty
                  ? null
                  : onEnviar,
              icon: enviando
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.send_outlined, size: 21),
            ),
          ),
        ],
      ),
    ),
  );
}
