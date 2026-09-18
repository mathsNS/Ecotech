import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/finance/finance_data.dart';
import '../../shared/widgets/app_back_button.dart';
import '../../shared/widgets/dashboard_widgets.dart';
import '../auth/auth_controller.dart';
import '../communication/widgets/communication_actions.dart';
import '../company/widgets/company_navigation.dart';
import '../company/widgets/company_states.dart';
import 'finance_controller.dart';

class RelatoriosScreen extends ConsumerStatefulWidget {
  const RelatoriosScreen({super.key});

  @override
  ConsumerState<RelatoriosScreen> createState() => _RelatoriosScreenState();
}

class _RelatoriosScreenState extends ConsumerState<RelatoriosScreen> {
  DateTime? _inicio;
  DateTime? _fim;
  bool _exportando = false;

  PeriodoRelatorio get _periodo => PeriodoRelatorio(inicio: _inicio, fim: _fim);

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(relatorioProvider(_periodo));
    final userType = ref.watch(authControllerProvider).valueOrNull?.tipo;
    return Scaffold(
      appBar: AppBar(
        leading: const AppBackButton(),
        title: const Text('Relatórios ambientais'),
        actions: const [CommunicationActions()],
      ),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(relatorioProvider(_periodo)),
        ),
        data: (relatorio) => RefreshIndicator(
          onRefresh: () => ref.refresh(relatorioProvider(_periodo).future),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              _FiltroPeriodo(
                inicio: _inicio,
                fim: _fim,
                onInicio: () => _selecionarData(true),
                onFim: () => _selecionarData(false),
                onLimpar: _inicio == null && _fim == null
                    ? null
                    : () => setState(() {
                        _inicio = null;
                        _fim = null;
                      }),
              ),
              const SizedBox(height: 14),
              _MetricasRelatorio(relatorio.metricas),
              const SizedBox(height: 14),
              _PnrsCard(relatorio.pnrs),
              const SizedBox(height: 14),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  onPressed: !relatorio.podeExportar || _exportando
                      ? null
                      : _exportar,
                  icon: _exportando
                      ? const SizedBox.square(
                          dimension: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.download_outlined),
                  label: Text(
                    relatorio.podeExportar
                        ? 'Exportar e compartilhar CSV'
                        : 'Exportação disponível no plano Professional',
                  ),
                ),
              ),
              const SizedBox(height: 22),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      'Solicitações finalizadas',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ),
                  Text('${relatorio.finalizadas.length} processadas'),
                ],
              ),
              const SizedBox(height: 8),
              if (relatorio.finalizadas.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(18),
                    child: Text(
                      'Nenhuma operação finalizada no período selecionado.',
                    ),
                  ),
                )
              else
                ...relatorio.finalizadas.map(_OperacaoRelatorio.new),
            ],
          ),
        ),
      ),
      bottomNavigationBar: userType == 'empresa'
          ? const CompanyNavigation(selectedIndex: 2)
          : null,
    );
  }

  Future<void> _selecionarData(bool inicio) async {
    final atual = inicio ? _inicio : _fim;
    final data = await showDatePicker(
      context: context,
      initialDate: atual ?? DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 1)),
    );
    if (data == null) return;
    setState(() {
      if (inicio) {
        _inicio = data;
        if (_fim != null && _fim!.isBefore(data)) _fim = data;
      } else {
        _fim = data;
        if (_inicio != null && _inicio!.isAfter(data)) _inicio = data;
      }
    });
  }

  Future<void> _exportar() async {
    setState(() => _exportando = true);
    try {
      final bytes = await ref
          .read(financeRepositoryProvider)
          .baixarRelatorioCsv(inicio: _inicio, fim: _fim);
      if (!mounted) return;
      final box = context.findRenderObject() as RenderBox?;
      await SharePlus.instance.share(
        ShareParams(
          title: 'Relatório ambiental EcoTech',
          files: [XFile.fromData(bytes, mimeType: 'text/csv')],
          fileNameOverrides: ['relatorio_ecotech.csv'],
          sharePositionOrigin: box == null
              ? null
              : box.localToGlobal(Offset.zero) & box.size,
        ),
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              error is ApiException
                  ? error.mensagem
                  : 'Não foi possível exportar o relatório.',
            ),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _exportando = false);
    }
  }
}

class _FiltroPeriodo extends StatelessWidget {
  const _FiltroPeriodo({
    required this.inicio,
    required this.fim,
    required this.onInicio,
    required this.onFim,
    required this.onLimpar,
  });

  final DateTime? inicio;
  final DateTime? fim;
  final VoidCallback onInicio;
  final VoidCallback onFim;
  final VoidCallback? onLimpar;

  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Período', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: onInicio,
                  icon: const Icon(Icons.calendar_today_outlined, size: 18),
                  label: Text(
                    inicio == null
                        ? 'Data inicial'
                        : AppFormatters.data(inicio),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: onFim,
                  icon: const Icon(Icons.event_outlined, size: 18),
                  label: Text(
                    fim == null ? 'Data final' : AppFormatters.data(fim),
                  ),
                ),
              ),
            ],
          ),
          if (onLimpar != null)
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: onLimpar,
                child: const Text('Limpar período'),
              ),
            ),
        ],
      ),
    ),
  );
}

class _MetricasRelatorio extends StatelessWidget {
  const _MetricasRelatorio(this.metricas);

  final MetricasRelatorioData metricas;

  @override
  Widget build(BuildContext context) {
    final itens = [
      (
        Icons.recycling,
        'Reciclado',
        metricas.pesoRecicladoKg,
        AppColors.success,
      ),
      (
        Icons.autorenew,
        'Reutilizado',
        metricas.pesoReutilizadoKg,
        AppColors.primary,
      ),
      (
        Icons.delete_outline,
        'Descarte controlado',
        metricas.pesoDescartadoKg,
        AppColors.warning,
      ),
      (
        Icons.eco_outlined,
        'Impacto evitado',
        metricas.impactoEvitadoKg,
        AppColors.primaryLight,
      ),
    ];
    return LayoutBuilder(
      builder: (context, constraints) {
        final largura = (constraints.maxWidth - 10) / 2;
        return Wrap(
          spacing: 10,
          runSpacing: 10,
          children: itens
              .map(
                (item) => SizedBox(
                  width: largura,
                  child: Card(
                    margin: EdgeInsets.zero,
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(item.$1, color: item.$4),
                          const SizedBox(height: 12),
                          Text(
                            '${AppFormatters.numero(item.$3, casas: 2)} kg',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          Text(
                            item.$2,
                            style: Theme.of(context).textTheme.bodyMedium,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              )
              .toList(),
        );
      },
    );
  }
}

class _PnrsCard extends StatelessWidget {
  const _PnrsCard(this.pnrs);

  final PnrsData pnrs;

  @override
  Widget build(BuildContext context) => DashboardSection(
    title: 'Conformidade PNRS',
    subtitle: pnrs.disponivel
        ? 'Indicadores de destinação e rastreabilidade.'
        : 'Disponível nos planos Professional e Enterprise.',
    child: pnrs.disponivel
        ? Row(
            children: [
              Expanded(
                child: _PnrsItem(
                  '${AppFormatters.numero(pnrs.destinacaoAdequada)}%',
                  'Destinação adequada',
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _PnrsItem(
                  '${AppFormatters.numero(pnrs.pesoGerenciadoKg)} kg',
                  'Peso gerenciado',
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _PnrsItem('${pnrs.solicitacoesAtendidas}', 'Atendidas'),
              ),
            ],
          )
        : const Row(
            children: [
              Icon(Icons.lock_outline, color: AppColors.textLight),
              SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Faça upgrade do plano para liberar PNRS e exportação CSV.',
                ),
              ),
            ],
          ),
  );
}

class _PnrsItem extends StatelessWidget {
  const _PnrsItem(this.valor, this.rotulo);

  final String valor;
  final String rotulo;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(valor, style: const TextStyle(fontWeight: FontWeight.w800)),
      const SizedBox(height: 3),
      Text(
        rotulo,
        style: const TextStyle(fontSize: 10, color: AppColors.textLight),
      ),
    ],
  );
}

class _OperacaoRelatorio extends StatelessWidget {
  const _OperacaoRelatorio(this.operacao);

  final OperacaoRelatorioData operacao;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 8),
    child: ExpansionTile(
      leading: const Icon(Icons.inventory_2_outlined),
      title: Text(operacao.cidadao),
      subtitle: Text(
        '${AppFormatters.numero(operacao.pesoKg, casas: 2)} kg · ${AppFormatters.dataTexto(operacao.data)}',
      ),
      trailing: StatusBadge(operacao.estado),
      childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
      children: [
        _Linha('Operação', '#${operacao.id.substring(0, 8)}'),
        _Linha('Tratamento', operacao.metodo ?? 'Não informado'),
        _Linha(
          'Impacto evitado',
          '${AppFormatters.numero(operacao.impactoKg)} kg CO₂',
        ),
      ],
    ),
  );
}

class _Linha extends StatelessWidget {
  const _Linha(this.rotulo, this.valor);
  final String rotulo;
  final String valor;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 8),
    child: Row(
      children: [
        Expanded(
          child: Text(rotulo, style: Theme.of(context).textTheme.bodyMedium),
        ),
        Text(valor, style: const TextStyle(fontWeight: FontWeight.w600)),
      ],
    ),
  );
}
