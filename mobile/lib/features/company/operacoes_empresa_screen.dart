import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../auth/auth_controller.dart';
import '../dashboard/dashboard_header.dart';
import '../operations/operations_widgets.dart';
import 'company_controller.dart';
import 'widgets/company_navigation.dart';
import 'widgets/company_states.dart';

class OperacoesEmpresaScreen extends ConsumerStatefulWidget {
  const OperacoesEmpresaScreen({super.key});

  @override
  ConsumerState<OperacoesEmpresaScreen> createState() =>
      _OperacoesEmpresaScreenState();
}

class _OperacoesEmpresaScreenState
    extends ConsumerState<OperacoesEmpresaScreen> {
  String _estado = '';
  int _pagina = 1;

  OperacoesConsulta get _consulta =>
      (estado: _estado, busca: '', pagina: _pagina);

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(operacoesEmpresaProvider(_consulta));
    final name = ref.watch(authControllerProvider).valueOrNull?.nome ?? 'EcoTech';
    return Scaffold(
      backgroundColor: operationsBackground,
      appBar: EcoTechDashboardHeader(name: name),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(operacoesEmpresaProvider(_consulta)),
        ),
        data: (data) => RefreshIndicator(
          onRefresh: () =>
              ref.refresh(operacoesEmpresaProvider(_consulta).future),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 27, 16, 28),
            children: [
              const Text(
                'Gerenciamento de\nOperações',
                style: TextStyle(
                  fontSize: 29,
                  height: 1.22,
                  fontWeight: FontWeight.w700,
                  color: operationsDark,
                  letterSpacing: -.8,
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Controle e acompanhamento de todas as solicitações',
                style: TextStyle(fontSize: 13.5, color: operationsMuted),
              ),
              const SizedBox(height: 21),
              _Metrics(data.estatisticas),
              const SizedBox(height: 25),
              OperationsFilters(
                selected: _estado,
                onSelected: (value) => setState(() {
                  _estado = value;
                  _pagina = 1;
                }),
              ),
              const SizedBox(height: 24),
              OperationsSectionTitle(total: data.total),
              const SizedBox(height: 14),
              if (data.operacoes.isEmpty)
                const CompanyEmpty(
                  message: 'Nenhuma operação encontrada para este estado.',
                )
              else
                ...data.operacoes.map(
                  (operation) => OperationsCard(
                    title: operation.cidadao,
                    subtitle: operation.pontoColeta ??
                        operation.empresa ??
                        'Destino ainda não definido',
                    status: operation.estado,
                    weight:
                        '${AppFormatters.numero(operation.pesoKg, casas: 1)} kg',
                    date: AppFormatters.data(operation.dataCriacao),
                    shortId: operation.id.substring(
                      0,
                      operation.id.length < 8 ? operation.id.length : 8,
                    ),
                    onDetails: () =>
                        context.push('/empresa/operacoes/${operation.id}'),
                    onSchedule: () => context.push(
                      '/solicitacoes/${operation.id}/agenda',
                    ),
                    onChat: () => context.push('/conversas/${operation.id}'),
                  ),
                ),
              if (data.totalPaginas > 1)
                OperationsPagination(
                  page: data.pagina,
                  totalPages: data.totalPaginas,
                  onPrevious: data.pagina > 1
                      ? () => setState(() => _pagina--)
                      : null,
                  onNext: data.pagina < data.totalPaginas
                      ? () => setState(() => _pagina++)
                      : null,
                ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const CompanyNavigation(selectedIndex: 1),
    );
  }
}

class _Metrics extends StatelessWidget {
  const _Metrics(this.stats);

  final Map<String, int> stats;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Row(
        children: [
          Expanded(
            child: OperationsMetric(
              icon: Icons.alarm_outlined,
              value: stats['pendentes'] ?? 0,
              label: 'Solicitações Pendentes',
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: OperationsMetric(
              icon: Icons.business_outlined,
              value: stats['em_coleta'] ?? 0,
              label: 'Em Coleta',
            ),
          ),
        ],
      ),
      const SizedBox(height: 10),
      Row(
        children: [
          Expanded(
            child: OperationsMetric(
              icon: Icons.settings_outlined,
              value: stats['processando'] ?? 0,
              label: 'Em Processamento',
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: OperationsMetric(
              icon: Icons.check_circle_outline,
              value: stats['finalizadas'] ?? 0,
              label: 'Finalizadas',
            ),
          ),
        ],
      ),
    ],
  );
}
