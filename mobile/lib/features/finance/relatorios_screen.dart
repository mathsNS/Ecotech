import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/finance/finance_data.dart';
import '../auth/auth_controller.dart';
import '../company/widgets/company_navigation.dart';
import '../company/widgets/company_states.dart';
import '../dashboard/dashboard_header.dart';
import '../operations/operations_widgets.dart';
import 'finance_controller.dart';

const _soft = Color(0xFFF3F7F4);
const _heading = TextStyle(
  fontSize: 19,
  fontWeight: FontWeight.w800,
  color: operationsDark,
);

class RelatoriosScreen extends ConsumerStatefulWidget {
  const RelatoriosScreen({super.key});

  @override
  ConsumerState<RelatoriosScreen> createState() => _RelatoriosScreenState();
}

class _RelatoriosScreenState extends ConsumerState<RelatoriosScreen> {
  DateTime? _inicio;
  DateTime? _fim;
  PeriodoRelatorio _periodo = const PeriodoRelatorio();
  bool _exportando = false;
  bool _mostrarTodas = false;
  static const _limiteInicial = 3;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(relatorioProvider(_periodo));
    final usuario = ref.watch(authControllerProvider).valueOrNull;
    return Scaffold(
      backgroundColor: operationsBackground,
      appBar: EcoTechDashboardHeader(name: usuario?.nome ?? 'EcoTech'),
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
            children: [
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 24, 16, 36),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Relatórios Ambientais',
                      style: TextStyle(
                        fontSize: 24,
                        fontWeight: FontWeight.w800,
                        color: operationsDark,
                        letterSpacing: -.7,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Indicadores e conformidade do período selecionado',
                      style: TextStyle(fontSize: 13, color: operationsMuted),
                    ),
                    const SizedBox(height: 20),
                    FilledButton.icon(
                      onPressed: !relatorio.podeExportar || _exportando
                          ? null
                          : _exportar,
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.primary,
                        shape: const StadiumBorder(),
                      ),
                      icon: _exportando
                          ? const SizedBox.square(
                              dimension: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.file_download_outlined, size: 18),
                      label: const Text(
                        'Exportar CSV',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                    if (!relatorio.podeExportar)
                      const Padding(
                        padding: EdgeInsets.only(top: 6),
                        child: Text(
                          'Exportação disponível nos planos Professional e Enterprise.',
                          style: TextStyle(
                            fontSize: 12,
                            color: operationsMuted,
                          ),
                        ),
                      ),
                    const SizedBox(height: 16),
                    _filtro(),
                    const SizedBox(height: 24),
                    _MetricasRelatorio(relatorio.metricas),
                    const SizedBox(height: 24),
                    _ResumoGeral(relatorio.metricas),
                    const SizedBox(height: 24),
                    Row(
                      children: [
                        const Expanded(
                          child: Text(
                            'Solicitações finalizadas',
                            style: _heading,
                          ),
                        ),
                        Text(
                          '${relatorio.finalizadas.length}',
                          style: const TextStyle(color: operationsMuted),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    if (relatorio.finalizadas.isEmpty)
                      const _ReportCard(
                        child: Text(
                          'Nenhuma operação finalizada no período selecionado.',
                        ),
                      )
                    else
                      ...relatorio.finalizadas
                          .take(
                            _mostrarTodas
                                ? relatorio.finalizadas.length
                                : _limiteInicial,
                          )
                          .map(
                            (operacao) => Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: _OperacaoRelatorio(operacao),
                            ),
                          ),
                    if (relatorio.finalizadas.length > _limiteInicial)
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: () =>
                              setState(() => _mostrarTodas = !_mostrarTodas),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: operationsDark,
                            backgroundColor: Colors.white,
                            side: const BorderSide(color: operationsBorder),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(16),
                            ),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                          icon: Icon(
                            _mostrarTodas
                                ? Icons.keyboard_arrow_up
                                : Icons.keyboard_arrow_down,
                            size: 20,
                          ),
                          label: Text(
                            _mostrarTodas
                                ? 'Mostrar menos'
                                : 'Mostrar mais (${relatorio.finalizadas.length - _limiteInicial} restantes)',
                          ),
                        ),
                      ),
                    const SizedBox(height: 24),
                    _PnrsCard(relatorio.pnrs),
                  ],
                ),
              ),
              const _ReportFooter(),
            ],
          ),
        ),
      ),
      bottomNavigationBar: usuario?.tipo == 'empresa'
          ? const CompanyNavigation(selectedIndex: 2)
          : null,
    );
  }

  Widget _filtro() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      LayoutBuilder(
        builder: (context, constraints) {
          final dates = Row(
            children: [
              Expanded(
                child: _DateField(
                  label: 'DE',
                  value: _inicio,
                  onTap: () => _selecionarData(true),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _DateField(
                  label: 'ATÉ',
                  value: _fim,
                  onTap: () => _selecionarData(false),
                ),
              ),
            ],
          );
          final button = FilledButton(
            onPressed: () => setState(() {
              _periodo = PeriodoRelatorio(inicio: _inicio, fim: _fim);
              _mostrarTodas = false;
            }),
            style: FilledButton.styleFrom(
              backgroundColor: AppColors.primary,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              shape: const StadiumBorder(),
            ),
            child: const Text(
              'Filtrar',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
            ),
          );
          if (constraints.maxWidth < 340 ||
              MediaQuery.textScalerOf(context).scale(12) > 16) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [dates, const SizedBox(height: 8), button],
            );
          }
          return Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Expanded(child: dates),
              const SizedBox(width: 8),
              button,
            ],
          );
        },
      ),
      if (_inicio != null ||
          _fim != null ||
          _periodo.inicio != null ||
          _periodo.fim != null)
        TextButton(
          onPressed: () => setState(() {
            _inicio = null;
            _fim = null;
            _periodo = const PeriodoRelatorio();
            _mostrarTodas = false;
          }),
          child: const Text('Limpar período'),
        ),
    ],
  );

  Future<void> _selecionarData(bool inicio) async {
    final data = await showDatePicker(
      context: context,
      initialDate: (inicio ? _inicio : _fim) ?? DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 1)),
    );
    if (data == null || !mounted) return;
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
          .baixarRelatorioCsv(inicio: _periodo.inicio, fim: _periodo.fim);
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

class _DateField extends StatelessWidget {
  const _DateField({
    required this.label,
    required this.value,
    required this.onTap,
  });
  final String label;
  final DateTime? value;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        label,
        style: const TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.w600,
          color: operationsMuted,
        ),
      ),
      const SizedBox(height: 6),
      OutlinedButton(
        onPressed: onTap,
        style: OutlinedButton.styleFrom(
          foregroundColor: operationsMuted,
          backgroundColor: Colors.white,
          side: const BorderSide(color: operationsBorder),
          shape: const StadiumBorder(),
          padding: const EdgeInsets.symmetric(horizontal: 10),
          minimumSize: const Size.fromHeight(40),
        ),
        child: Row(
          children: [
            const Icon(Icons.calendar_month_outlined, size: 16),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                value == null ? 'dd/mm/aaaa' : AppFormatters.data(value),
                style: const TextStyle(fontSize: 11),
              ),
            ),
          ],
        ),
      ),
    ],
  );
}

class _ReportCard extends StatelessWidget {
  const _ReportCard({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(22),
      border: Border.all(color: const Color(0xFFF0F1F2)),
      boxShadow: const [
        BoxShadow(
          color: Color(0x10000000),
          blurRadius: 2,
          offset: Offset(0, 2),
        ),
      ],
    ),
    child: child,
  );
}

class _MetricasRelatorio extends StatelessWidget {
  const _MetricasRelatorio(this.metricas);
  final MetricasRelatorioData metricas;

  @override
  Widget build(BuildContext context) {
    final itens = [
      (
        Icons.delete_outline,
        'Peso Reciclado',
        metricas.pesoRecicladoKg,
        const Color(0xFF2DA569),
        const Color(0xFFE3F1E9),
      ),
      (
        Icons.devices_outlined,
        'Peso Reutilizado',
        metricas.pesoReutilizadoKg,
        const Color(0xFF26764D),
        const Color(0xFFE0EAE4),
      ),
      (
        Icons.recycling,
        'Descarte Controlado',
        metricas.pesoDescartadoKg,
        const Color(0xFF79520D),
        const Color(0xFFFFF7E5),
      ),
      (
        Icons.eco_outlined,
        'Impacto Evitado',
        metricas.impactoEvitadoKg,
        const Color(0xFF2DA569),
        const Color(0xFFE3F1E9),
      ),
    ];
    return LayoutBuilder(
      builder: (context, constraints) => Wrap(
        spacing: 10,
        runSpacing: 12,
        children: [
          for (var i = 0; i < itens.length; i++)
            SizedBox(
              width: (constraints.maxWidth - 10) / 2,
              child: _ReportCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CircleAvatar(
                      radius: 20,
                      backgroundColor: itens[i].$5,
                      child: Icon(itens[i].$1, color: itens[i].$4, size: 22),
                    ),
                    const SizedBox(height: 14),
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      alignment: Alignment.centerLeft,
                      child: Text(
                        '${AppFormatters.numero(itens[i].$3)} kg${i == 3 ? ' CO₂' : ''}',
                        style: const TextStyle(
                          fontSize: 21,
                          fontWeight: FontWeight.w800,
                          color: operationsDark,
                          letterSpacing: -.6,
                        ),
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      itens[i].$2,
                      style: const TextStyle(
                        fontSize: 11,
                        color: operationsMuted,
                      ),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _ResumoGeral extends StatelessWidget {
  const _ResumoGeral(this.metricas);
  final MetricasRelatorioData metricas;

  @override
  Widget build(BuildContext context) => _ReportCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Resumo Geral', style: _heading),
        const SizedBox(height: 18),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: _StatTile(
                label: 'TOTAL DE\nSOLICITAÇÕES',
                value: '${metricas.totalSolicitacoes}',
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _StatTile(
                label: 'PESO TOTAL\nPROCESSADO',
                value: '${AppFormatters.numero(metricas.pesoTotalKg)} kg',
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: _StatTile(
                label: 'TAXA DE\nRECICLAGEM',
                value: '${AppFormatters.numero(metricas.taxaReciclagem)}%',
              ),
            ),
          ],
        ),
      ],
    ),
  );
}

class _StatTile extends StatelessWidget {
  const _StatTile({
    required this.label,
    required this.value,
    this.caption,
    this.compact = false,
  });
  final String label;
  final String value;
  final String? caption;
  final bool compact;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: EdgeInsets.symmetric(horizontal: 6, vertical: compact ? 10 : 14),
    decoration: BoxDecoration(
      color: _soft,
      borderRadius: BorderRadius.circular(17),
    ),
    child: Column(
      children: [
        if (!compact) ...[
          Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.w500,
              color: operationsMuted,
            ),
          ),
          const SizedBox(height: 8),
        ],
        Text(
          value,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: compact ? 12 : 20,
            fontWeight: FontWeight.w800,
            color: operationsDark,
            letterSpacing: -.4,
          ),
        ),
        if (compact || caption != null) ...[
          const SizedBox(height: 4),
          Text(
            compact ? label : caption!,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 10, color: operationsMuted),
          ),
        ],
      ],
    ),
  );
}

class _PnrsCard extends StatelessWidget {
  const _PnrsCard(this.pnrs);
  final PnrsData pnrs;

  @override
  Widget build(BuildContext context) => _ReportCard(
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          alignment: WrapAlignment.spaceBetween,
          crossAxisAlignment: WrapCrossAlignment.center,
          spacing: 12,
          runSpacing: 8,
          children: [
            const Text('Conformidade PNRS', style: _heading),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(
                color: operationsSoftGreen,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    pnrs.disponivel
                        ? Icons.check_circle_outline
                        : Icons.lock_outline,
                    size: 13,
                    color: AppColors.primary,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    pnrs.disponivel ? 'Disponível' : 'Restrito',
                    style: const TextStyle(
                      fontSize: 10,
                      color: AppColors.primary,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 18),
        if (pnrs.disponivel) ...[
          _StatTile(
            label: 'DESTINAÇÃO ADEQUADA',
            value: '${AppFormatters.numero(pnrs.destinacaoAdequada)}%',
            caption: 'Reciclado + Reutilizado',
          ),
          const SizedBox(height: 12),
          _StatTile(
            label: 'PESO TOTAL GERENCIADO',
            value: '${AppFormatters.numero(pnrs.pesoGerenciadoKg)} kg',
            caption: 'No período selecionado',
          ),
          const SizedBox(height: 12),
          _StatTile(
            label: 'SOLICITAÇÕES ATENDIDAS',
            value: '${pnrs.solicitacoesAtendidas}',
            caption: 'No período selecionado',
          ),
        ] else
          const Text(
            'Faça upgrade do plano para liberar PNRS e exportação CSV.',
            style: TextStyle(color: operationsMuted),
          ),
      ],
    ),
  );
}

class _OperacaoRelatorio extends StatelessWidget {
  const _OperacaoRelatorio(this.operacao);
  final OperacaoRelatorioData operacao;

  @override
  Widget build(BuildContext context) {
    final id = operacao.id.length > 8
        ? '${operacao.id.substring(0, 8)}...'
        : operacao.id;
    return _ReportCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Text(
                  operacao.cidadao,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w800,
                    color: operationsDark,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              OperationsStatus(operacao.estado),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            'ID $id',
            style: const TextStyle(fontSize: 11, color: operationsMuted),
          ),
          const SizedBox(height: 12),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _StatTile(
                  label: 'kg',
                  value: AppFormatters.numero(operacao.pesoKg),
                  compact: true,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _StatTile(
                  label: 'impacto',
                  value: AppFormatters.numero(operacao.impactoKg),
                  compact: true,
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _StatTile(
                  label: 'método',
                  value: operacao.metodo ?? 'Não informado',
                  compact: true,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            AppFormatters.dataTexto(operacao.data),
            style: const TextStyle(fontSize: 11, color: operationsMuted),
          ),
        ],
      ),
    );
  }
}

class _ReportFooter extends StatelessWidget {
  const _ReportFooter();

  @override
  Widget build(BuildContext context) => Container(
    color: const Color(0xFF101315),
    width: double.infinity,
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 36),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'ECOTECH',
          style: TextStyle(
            fontSize: 19,
            fontWeight: FontWeight.w800,
            color: AppColors.primary,
          ),
        ),
        const SizedBox(height: 16),
        const Text(
          'Relatórios claros para uma gestão ambiental responsável.',
          style: TextStyle(fontSize: 13, height: 1.7, color: Color(0xFFCCD0CE)),
        ),
        const SizedBox(height: 24),
        Text(
          '© ${DateTime.now().year} EcoTech. Todos os direitos reservados.',
          style: const TextStyle(fontSize: 11, color: Color(0xFF9CA3A0)),
        ),
      ],
    ),
  );
}
