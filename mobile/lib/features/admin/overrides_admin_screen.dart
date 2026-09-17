import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/admin/admin_data.dart';
import '../communication/widgets/communication_actions.dart';
import '../company/widgets/company_states.dart';
import 'admin_controller.dart';
import 'widgets/admin_navigation.dart';

class OverridesAdminScreen extends ConsumerStatefulWidget {
  const OverridesAdminScreen({super.key});

  @override
  ConsumerState<OverridesAdminScreen> createState() => _OverridesAdminScreenState();
}

class _OverridesAdminScreenState extends ConsumerState<OverridesAdminScreen> {
  String? _processando;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(overridesAdminProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Overrides pendentes'),
        actions: const [CommunicationActions()],
      ),
      bottomNavigationBar: const AdminNavigation(selectedIndex: 3),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(overridesAdminProvider),
        ),
        data: (itens) => RefreshIndicator(
          onRefresh: () => ref.refresh(overridesAdminProvider.future),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 30),
            children: [
              _ResumoOverride(itens.length),
              const SizedBox(height: 12),
              if (itens.isEmpty)
                const CompanyEmpty(message: 'Nenhum override aguardando decisão.')
              else
                ...itens.map(
                  (item) => _OverrideCard(
                    item,
                    processando: _processando == item.solicitacaoId,
                    onAprovar: () => _decidir(item, 'aprovar'),
                    onRejeitar: () => _decidir(item, 'rejeitar'),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _decidir(OverrideAdminData item, String decisao) async {
    final aprovar = decisao == 'aprovar';
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(aprovar ? 'Aprovar override' : 'Rejeitar override'),
        content: Text(
          aprovar
              ? 'Confirmar o valor proposto de ${AppFormatters.moeda(item.valorProposto)}?'
              : 'Rejeitar a proposta e aplicar ${AppFormatters.moeda(item.valorRecalculado)}?',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Cancelar')),
          ElevatedButton(onPressed: () => Navigator.pop(dialogContext, true), child: Text(aprovar ? 'Aprovar' : 'Rejeitar')),
        ],
      ),
    );
    if (confirmar != true) return;
    setState(() => _processando = item.solicitacaoId);
    try {
      await ref
          .read(adminRepositoryProvider)
          .decidirOverride(item.solicitacaoId, decisao);
      ref.invalidate(overridesAdminProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(aprovar ? 'Override aprovado.' : 'Override rejeitado.')),
        );
      }
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error is ApiException ? error.mensagem : 'Não foi possível registrar a decisão.')),
        );
      }
    } finally {
      if (mounted) setState(() => _processando = null);
    }
  }
}

class _ResumoOverride extends StatelessWidget {
  const _ResumoOverride(this.total);
  final int total;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: total > 0 ? AppColors.warning.withValues(alpha: .12) : AppColors.secondary,
      borderRadius: BorderRadius.circular(12),
    ),
    child: Row(
      children: [
        Icon(total > 0 ? Icons.pending_actions_outlined : Icons.check_circle_outline),
        const SizedBox(width: 10),
        Text('$total aguardando aprovação', style: const TextStyle(fontWeight: FontWeight.w700)),
      ],
    ),
  );
}

class _OverrideCard extends StatelessWidget {
  const _OverrideCard(
    this.item, {
    required this.processando,
    required this.onAprovar,
    required this.onRejeitar,
  });
  final OverrideAdminData item;
  final bool processando;
  final VoidCallback onAprovar;
  final VoidCallback onRejeitar;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 10),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text('#${item.solicitacaoId.substring(0, 8)}', style: Theme.of(context).textTheme.titleMedium),
              ),
              Text(AppFormatters.dataHoraTexto(item.dataCriacao)),
            ],
          ),
          const SizedBox(height: 8),
          _Linha('Cidadão', item.cidadao),
          _Linha('Empresa', item.empresa),
          _Linha('Estado declarado', item.estadoProduto.replaceAll('_', ' ')),
          const Divider(height: 22),
          _Linha('Valor base', AppFormatters.moeda(item.valorBase)),
          _Linha('Mínimo sucata', AppFormatters.moeda(item.valorMinimo)),
          _Linha('Limite automático', AppFormatters.moeda(item.limiteOverride)),
          _Linha('Valor proposto', AppFormatters.moeda(item.valorProposto), destaque: true),
          const SizedBox(height: 8),
          Text('Justificativa', style: Theme.of(context).textTheme.bodyMedium),
          Text(item.justificativa.isEmpty ? 'Não informada' : item.justificativa),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: processando ? null : onRejeitar,
                  icon: const Icon(Icons.close),
                  label: const Text('Rejeitar'),
                ),
              ),
              const SizedBox(width: 9),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed: processando ? null : onAprovar,
                  icon: processando
                      ? const SizedBox.square(dimension: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.check),
                  label: const Text('Aprovar'),
                ),
              ),
            ],
          ),
        ],
      ),
    ),
  );
}

class _Linha extends StatelessWidget {
  const _Linha(this.rotulo, this.valor, {this.destaque = false});
  final String rotulo;
  final String valor;
  final bool destaque;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 7),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(child: Text(rotulo, style: Theme.of(context).textTheme.bodyMedium)),
        Text(
          valor,
          textAlign: TextAlign.right,
          style: TextStyle(fontWeight: destaque ? FontWeight.w800 : FontWeight.w600, color: destaque ? AppColors.primary : null),
        ),
      ],
    ),
  );
}
