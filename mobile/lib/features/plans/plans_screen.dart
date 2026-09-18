import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/plans/plans_data.dart';
import '../communication/widgets/communication_actions.dart';
import '../company/widgets/company_navigation.dart';
import '../company/widgets/company_states.dart';
import 'plans_controller.dart';

class PlansScreen extends ConsumerStatefulWidget {
  const PlansScreen({super.key});

  @override
  ConsumerState<PlansScreen> createState() => _PlansScreenState();
}

class _PlansScreenState extends ConsumerState<PlansScreen> {
  String? _changingPlan;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(plansControllerProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Planos EcoTech'),
        actions: const [CommunicationActions()],
      ),
      bottomNavigationBar: const CompanyNavigation(selectedIndex: 4),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.read(plansControllerProvider.notifier).reload(),
        ),
        data: (data) => RefreshIndicator(
          onRefresh: () => ref.read(plansControllerProvider.notifier).reload(),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 18, 16, 32),
            children: [
              Text(
                'Escolha o plano ideal para sua empresa',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 6),
              Text(
                'Compare limites e recursos antes de confirmar a alteração.',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              if (data.demoEnvironment) ...[
                const SizedBox(height: 14),
                const _DemoNotice(),
              ],
              const SizedBox(height: 18),
              ...data.plans.map(
                (plan) => Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: _PlanCard(
                    plan: plan,
                    current: plan.id == data.currentPlan,
                    changing: _changingPlan == plan.id,
                    onSelect: () => _confirmChange(data, plan),
                  ),
                ),
              ),
              _EffectiveFeatures(data.featureFlags),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _confirmChange(PlansData data, PlanData plan) async {
    if (plan.id == data.currentPlan || _changingPlan != null) return;
    final current = data.plans
        .where((item) => item.id == data.currentPlan)
        .firstOrNull;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Alterar para ${plan.name}?'),
        content: Text(
          'Seu plano mudará de ${current?.name ?? data.currentPlan} para '
          '${plan.name}. A alteração é imediata neste ambiente de demonstração.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirmar alteração'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _changingPlan = plan.id);
    try {
      await ref.read(plansControllerProvider.notifier).changePlan(plan.id);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Plano ${plan.name} ativado com sucesso.')),
      );
    } catch (error) {
      if (!mounted) return;
      final message = error is ApiException
          ? error.mensagem
          : 'Não foi possível alterar o plano.';
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(message)));
    } finally {
      if (mounted) setState(() => _changingPlan = null);
    }
  }
}

class _DemoNotice extends StatelessWidget {
  const _DemoNotice();

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: AppColors.secondary,
      borderRadius: BorderRadius.circular(12),
    ),
    child: const Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(Icons.info_outline, color: AppColors.primary),
        SizedBox(width: 10),
        Expanded(
          child: Text(
            'Ambiente de demonstração: a troca é imediata e não realiza cobrança.',
          ),
        ),
      ],
    ),
  );
}

class _PlanCard extends StatelessWidget {
  const _PlanCard({
    required this.plan,
    required this.current,
    required this.changing,
    required this.onSelect,
  });

  final PlanData plan;
  final bool current;
  final bool changing;
  final VoidCallback onSelect;

  String get _asset => switch (plan.id) {
    'professional' => 'assets/images/plano-pro.png',
    'enterprise' => 'assets/images/plano-enterprise.png',
    _ => 'assets/images/plano-free.png',
  };

  @override
  Widget build(BuildContext context) => Semantics(
    container: true,
    label: '${plan.name}, ${AppFormatters.moeda(plan.monthlyPrice)} por mês',
    child: Card(
      color: current ? AppColors.secondary : null,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: current || plan.highlighted
              ? AppColors.primary
              : Theme.of(context).dividerColor,
          width: current ? 2 : 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Image.asset(_asset, width: 54, height: 54),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        plan.name,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      Text(
                        '${AppFormatters.moeda(plan.monthlyPrice)}/mês',
                        style: const TextStyle(
                          color: AppColors.primary,
                          fontWeight: FontWeight.w800,
                        ),
                      ),
                    ],
                  ),
                ),
                if (current)
                  const Chip(
                    avatar: Icon(Icons.check_circle, size: 18),
                    label: Text('Atual'),
                  )
                else if (plan.highlighted)
                  const Chip(label: Text('Recomendado')),
              ],
            ),
            const SizedBox(height: 14),
            Text(
              plan.monthlyRequestLimit == null
                  ? 'Solicitações mensais ilimitadas'
                  : 'Até ${plan.monthlyRequestLimit} solicitações por mês',
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 10),
            ...plan.features.map(
              (feature) => Padding(
                padding: const EdgeInsets.only(bottom: 7),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.check_circle_outline,
                      size: 19,
                      color: AppColors.primary,
                    ),
                    const SizedBox(width: 8),
                    Expanded(child: Text(feature)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 10),
            SizedBox(
              width: double.infinity,
              child: current
                  ? const OutlinedButton(
                      onPressed: null,
                      child: Text('Plano atual'),
                    )
                  : ElevatedButton(
                      onPressed: changing ? null : onSelect,
                      child: changing
                          ? const SizedBox.square(
                              dimension: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('Selecionar plano'),
                    ),
            ),
          ],
        ),
      ),
    ),
  );
}

class _EffectiveFeatures extends StatelessWidget {
  const _EffectiveFeatures(this.flags);

  final Map<String, bool> flags;

  @override
  Widget build(BuildContext context) {
    final enabled = flags.entries.where((item) => item.value).toList();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Recursos ativos',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 10),
            if (enabled.isEmpty)
              const Text('Recursos essenciais do plano Free.')
            else
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: enabled
                    .map(
                      (item) => Chip(
                        avatar: const Icon(Icons.check, size: 17),
                        label: Text(_flagLabel(item.key)),
                      ),
                    )
                    .toList(),
              ),
          ],
        ),
      ),
    );
  }

  static String _flagLabel(String key) => switch (key) {
    'solicitacoes_ilimitadas' => 'Solicitações ilimitadas',
    'notificacoes_avancadas' => 'Notificações avançadas',
    'historico_completo' => 'Histórico completo',
    'relatorio_pnrs' => 'Relatório PNRS',
    'exportacao_dados' => 'Exportação de dados',
    'mtr' => 'MTR',
    'dashboard_esg' => 'Dashboard ESG',
    'api_integracao' => 'API de integração',
    'multiplos_pontos' => 'Múltiplos pontos',
    'relatorios_automaticos' => 'Relatórios automáticos',
    'analytics_regional' => 'Analytics regional',
    'suporte_dedicado' => 'Suporte dedicado',
    _ => key.replaceAll('_', ' '),
  };
}
