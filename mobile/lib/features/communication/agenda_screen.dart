import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/communication/communication_data.dart';
import '../../shared/widgets/app_back_button.dart';
import '../company/widgets/company_states.dart';
import 'communication_controller.dart';

class AgendaScreen extends ConsumerStatefulWidget {
  const AgendaScreen({required this.solicitacaoId, super.key});

  final String solicitacaoId;

  @override
  ConsumerState<AgendaScreen> createState() => _AgendaScreenState();
}

class _AgendaScreenState extends ConsumerState<AgendaScreen> {
  bool _processando = false;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(agendaProvider(widget.solicitacaoId));
    return Scaffold(
      appBar: AppBar(
        leading: const AppBackButton(),
        title: const Text('Agenda da coleta'),
      ),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(agendaProvider(widget.solicitacaoId)),
        ),
        data: (agenda) => RefreshIndicator(
          onRefresh: () =>
              ref.refresh(agendaProvider(widget.solicitacaoId).future),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              _ResumoAgenda(agenda),
              const SizedBox(height: 12),
              _AcoesAgenda(
                agenda: agenda,
                processando: _processando,
                onPropor: _propor,
                onAceitar: _aceitar,
                onRejeitar: _rejeitar,
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: () =>
                    context.push('/conversas/${widget.solicitacaoId}'),
                icon: const Icon(Icons.chat_bubble_outline),
                label: const Text('Abrir conversa desta coleta'),
              ),
              const SizedBox(height: 20),
              Text(
                'Histórico da agenda',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              if (agenda.historico.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('Ainda não há alterações de horário.'),
                  ),
                )
              else
                ...agenda.historico.reversed.map(_EventoAgenda.new),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _propor() async {
    final periodo = await showDialog<({DateTime inicio, DateTime fim})>(
      context: context,
      builder: (_) => const _PropostaDialog(),
    );
    if (periodo == null || !mounted) return;
    await _executar(
      () => ref
          .read(communicationRepositoryProvider)
          .proporHorario(widget.solicitacaoId, periodo.inicio, periodo.fim),
      'Proposta enviada.',
    );
  }

  Future<void> _aceitar() => _executar(
    () => ref
        .read(communicationRepositoryProvider)
        .aceitarHorario(widget.solicitacaoId),
    'Horário confirmado.',
  );

  Future<void> _rejeitar() => _executar(
    () => ref
        .read(communicationRepositoryProvider)
        .rejeitarHorario(widget.solicitacaoId),
    'Proposta recusada. Envie uma nova sugestão quando desejar.',
  );

  Future<void> _executar(
    Future<AgendaData> Function() acao,
    String sucesso,
  ) async {
    setState(() => _processando = true);
    try {
      await acao();
      ref.invalidate(agendaProvider(widget.solicitacaoId));
      ref.invalidate(notificacoesProvider);
      ref.invalidate(badgesProvider);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(sucesso)));
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_mensagemErro(error))));
      }
    } finally {
      if (mounted) setState(() => _processando = false);
    }
  }

  String _mensagemErro(Object error) => error is ApiException
      ? error.mensagem
      : 'Não foi possível atualizar a agenda.';
}

class _ResumoAgenda extends StatelessWidget {
  const _ResumoAgenda(this.agenda);

  final AgendaData agenda;

  @override
  Widget build(BuildContext context) {
    final confirmado = agenda.inicioConfirmado != null;
    final proposta = agenda.propostaInicio != null && !confirmado;
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const CircleAvatar(
                  backgroundColor: AppColors.secondary,
                  child: Icon(
                    Icons.calendar_month_outlined,
                    color: AppColors.primary,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        agenda.cidadao,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      Text(
                        '#${agenda.solicitacaoId.substring(0, 8)} · ${agenda.estado}',
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const Divider(height: 28),
            _LinhaPeriodo(
              titulo: 'Janela solicitada',
              inicio: agenda.janelaInicio,
              fim: agenda.janelaFim,
            ),
            if (proposta) ...[
              const SizedBox(height: 14),
              _LinhaPeriodo(
                titulo: 'Proposta atual',
                inicio: agenda.propostaInicio,
                fim: agenda.propostaFim,
                destaque: true,
              ),
              const SizedBox(height: 5),
              Text(
                'Enviada por ${agenda.propostaAutorNome ?? 'participante'} '
                '(${_tipo(agenda.propostaAutorTipo)})',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
            if (confirmado) ...[
              const SizedBox(height: 14),
              _LinhaPeriodo(
                titulo: 'Horário confirmado',
                inicio: agenda.inicioConfirmado,
                fim: agenda.fimConfirmado,
                destaque: true,
              ),
            ],
          ],
        ),
      ),
    );
  }

  static String _tipo(String? tipo) => switch (tipo) {
    'cidadao' => 'cidadão',
    'empresa' => 'empresa',
    _ => 'sistema',
  };
}

class _LinhaPeriodo extends StatelessWidget {
  const _LinhaPeriodo({
    required this.titulo,
    required this.inicio,
    required this.fim,
    this.destaque = false,
  });

  final String titulo;
  final String? inicio;
  final String? fim;
  final bool destaque;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: destaque ? const EdgeInsets.all(12) : EdgeInsets.zero,
    decoration: destaque
        ? BoxDecoration(
            color: AppColors.secondary,
            borderRadius: BorderRadius.circular(10),
          )
        : null,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(titulo, style: const TextStyle(fontWeight: FontWeight.w700)),
        const SizedBox(height: 4),
        Text(_periodo(inicio, fim)),
      ],
    ),
  );

  static String _periodo(String? inicio, String? fim) {
    if (inicio == null || inicio.isEmpty) return 'Não informado';
    final textoInicio = AppFormatters.dataHoraTexto(inicio);
    if (fim == null || fim.isEmpty) return textoInicio;
    final dataInicio = DateTime.tryParse(inicio);
    final dataFim = DateTime.tryParse(fim);
    if (dataInicio != null &&
        dataFim != null &&
        dataInicio.year == dataFim.year &&
        dataInicio.month == dataFim.month &&
        dataInicio.day == dataFim.day) {
      final horaFim =
          '${dataFim.hour.toString().padLeft(2, '0')}:'
          '${dataFim.minute.toString().padLeft(2, '0')}';
      return '$textoInicio até $horaFim';
    }
    return '$textoInicio até ${AppFormatters.dataHoraTexto(fim)}';
  }
}

class _AcoesAgenda extends StatelessWidget {
  const _AcoesAgenda({
    required this.agenda,
    required this.processando,
    required this.onPropor,
    required this.onAceitar,
    required this.onRejeitar,
  });

  final AgendaData agenda;
  final bool processando;
  final VoidCallback onPropor;
  final VoidCallback onAceitar;
  final VoidCallback onRejeitar;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      if (agenda.podeAceitar)
        ElevatedButton.icon(
          onPressed: processando ? null : onAceitar,
          icon: const Icon(Icons.check_circle_outline),
          label: const Text('Aceitar horário'),
        ),
      if (agenda.podeRejeitar) ...[
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: processando ? null : onRejeitar,
          icon: const Icon(Icons.cancel_outlined),
          label: const Text('Recusar proposta'),
        ),
      ],
      if (agenda.podePropor) ...[
        const SizedBox(height: 8),
        OutlinedButton.icon(
          onPressed: processando ? null : onPropor,
          icon: const Icon(Icons.edit_calendar_outlined),
          label: const Text('Propor outro horário'),
        ),
      ],
      if (!agenda.podeAceitar && !agenda.podeRejeitar && !agenda.podePropor)
        const Text(
          'O horário já está confirmado e não possui ações pendentes.',
        ),
    ],
  );
}

class _EventoAgenda extends StatelessWidget {
  const _EventoAgenda(this.evento);

  final EventoAgendaData evento;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 8),
    child: ListTile(
      leading: const Icon(Icons.history),
      title: Text(_acao(evento.acao)),
      subtitle: Text(
        '${evento.autorNome} (${_tipo(evento.autorTipo)})\n'
        '${AppFormatters.dataHoraTexto(evento.criadoEm)}'
        '${evento.inicio == null ? '' : '\n${_LinhaPeriodo._periodo(evento.inicio, evento.fim)}'}',
      ),
      isThreeLine: evento.inicio != null,
    ),
  );

  static String _acao(String acao) => switch (acao) {
    'PROPOSTA' => 'Novo horário proposto',
    'ACEITE' => 'Horário aceito',
    'RECUSA' => 'Proposta recusada',
    'CRIACAO' => 'Agenda criada',
    _ => acao.replaceAll('_', ' ').toLowerCase(),
  };

  static String _tipo(String tipo) => switch (tipo) {
    'cidadao' => 'cidadão',
    'empresa' => 'empresa',
    _ => 'sistema',
  };
}

class _PropostaDialog extends StatefulWidget {
  const _PropostaDialog();

  @override
  State<_PropostaDialog> createState() => _PropostaDialogState();
}

class _PropostaDialogState extends State<_PropostaDialog> {
  late DateTime inicio;
  late DateTime fim;

  @override
  void initState() {
    super.initState();
    final amanha = DateTime.now().add(const Duration(days: 1));
    inicio = DateTime(amanha.year, amanha.month, amanha.day, 9);
    fim = inicio.add(const Duration(hours: 2));
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Propor horário'),
    content: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        ListTile(
          contentPadding: EdgeInsets.zero,
          leading: const Icon(Icons.event_available_outlined),
          title: const Text('Início'),
          subtitle: Text(AppFormatters.dataHoraTexto(inicio.toIso8601String())),
          onTap: () => _selecionar(true),
        ),
        ListTile(
          contentPadding: EdgeInsets.zero,
          leading: const Icon(Icons.event_busy_outlined),
          title: const Text('Fim'),
          subtitle: Text(AppFormatters.dataHoraTexto(fim.toIso8601String())),
          onTap: () => _selecionar(false),
        ),
        if (!fim.isAfter(inicio))
          const Text(
            'O fim precisa ser posterior ao início.',
            style: TextStyle(color: AppColors.error),
          ),
      ],
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context),
        child: const Text('Cancelar'),
      ),
      ElevatedButton(
        onPressed: fim.isAfter(inicio)
            ? () => Navigator.pop(context, (inicio: inicio, fim: fim))
            : null,
        child: const Text('Enviar proposta'),
      ),
    ],
  );

  Future<void> _selecionar(bool selecionaInicio) async {
    final atual = selecionaInicio ? inicio : fim;
    final data = await showDatePicker(
      context: context,
      initialDate: atual,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (data == null || !mounted) return;
    final hora = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(atual),
    );
    if (hora == null) return;
    final valor = DateTime(
      data.year,
      data.month,
      data.day,
      hora.hour,
      hora.minute,
    );
    setState(() {
      if (selecionaInicio) {
        inicio = valor;
        if (!fim.isAfter(inicio)) fim = inicio.add(const Duration(hours: 2));
      } else {
        fim = valor;
      }
    });
  }
}
