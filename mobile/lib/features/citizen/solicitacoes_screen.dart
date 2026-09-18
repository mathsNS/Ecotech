import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../auth/auth_controller.dart';
import '../dashboard/dashboard_header.dart';
import '../operations/operations_widgets.dart';
import 'citizen_controller.dart';
import 'widgets/citizen_navigation.dart';
import 'widgets/citizen_states.dart';

class SolicitacoesScreen extends ConsumerStatefulWidget {
  const SolicitacoesScreen({super.key});

  @override
  ConsumerState<SolicitacoesScreen> createState() => _SolicitacoesScreenState();
}

class _SolicitacoesScreenState extends ConsumerState<SolicitacoesScreen> {
  String _estado = '';

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(solicitacoesProvider(_estado));
    final name = ref.watch(authControllerProvider).valueOrNull?.nome ?? 'EcoTech';
    return Scaffold(
      backgroundColor: operationsBackground,
      appBar: EcoTechDashboardHeader(name: name),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CitizenError(
          error: error,
          onRetry: () => ref.invalidate(solicitacoesProvider(_estado)),
        ),
        data: (page) => RefreshIndicator(
          onRefresh: () => ref.refresh(solicitacoesProvider(_estado).future),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 27, 16, 100),
            children: [
              const Text(
                'Minhas\nOperações',
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
                'Acompanhe todas as suas solicitações de descarte',
                style: TextStyle(fontSize: 13.5, color: operationsMuted),
              ),
              const SizedBox(height: 21),
              _CitizenMetrics(page.estatisticas),
              const SizedBox(height: 25),
              OperationsFilters(
                selected: _estado,
                onSelected: (value) => setState(() => _estado = value),
              ),
              const SizedBox(height: 24),
              OperationsSectionTitle(total: page.total),
              const SizedBox(height: 14),
              if (page.itens.isEmpty)
                CitizenEmpty(
                  message: 'Nenhuma solicitação encontrada para este estado.',
                  action: FilledButton(
                    onPressed: () => context.push('/solicitacoes/nova'),
                    child: const Text('Criar solicitação'),
                  ),
                )
              else
                ...page.itens.map(
                  (request) => OperationsCard(
                    title: 'Solicitação #${_shortId(request.id)}',
                    subtitle: request.pontoColeta ??
                        request.empresa ??
                        'Empresa ainda não definida',
                    status: request.estado,
                    weight:
                        '${AppFormatters.numero(request.pesoExibidoKg, casas: 1)} kg',
                    date: AppFormatters.data(request.dataCriacao),
                    shortId: _shortId(request.id),
                    onDetails: () =>
                        context.push('/solicitacoes/${request.id}'),
                    onSchedule: () =>
                        context.push('/solicitacoes/${request.id}/agenda'),
                    onChat: () => context.push('/conversas/${request.id}'),
                  ),
                ),
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/solicitacoes/nova'),
        backgroundColor: operationsDeepGreen,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add),
        label: const Text('Nova solicitação'),
      ),
      bottomNavigationBar: const CitizenNavigation(selectedIndex: 1),
    );
  }

  static String _shortId(String id) =>
      id.substring(0, id.length < 8 ? id.length : 8);
}

class _CitizenMetrics extends StatelessWidget {
  const _CitizenMetrics(this.stats);

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
              icon: Icons.local_shipping_outlined,
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
