import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/company/company_data.dart';
import '../dashboard/dashboard_controller.dart';
import 'company_controller.dart';
import 'widgets/company_navigation.dart';
import 'widgets/company_states.dart';

class OportunidadesEmpresaScreen extends ConsumerWidget {
  const OportunidadesEmpresaScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(oportunidadesEmpresaProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Oportunidades')),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(oportunidadesEmpresaProvider),
        ),
        data: (oportunidades) => RefreshIndicator(
          onRefresh: () => ref.refresh(oportunidadesEmpresaProvider.future),
          child: oportunidades.isEmpty
              ? ListView(
                  children: [
                    const SizedBox(height: 110),
                    CompanyEmpty(
                      message: 'Nenhuma oportunidade ativa agora. Verifique se suas bases estão ativas e atualize novamente em instantes.',
                      action: OutlinedButton.icon(
                        onPressed: () => context.go('/empresa/bases'),
                        icon: const Icon(Icons.warehouse_outlined),
                        label: const Text('Revisar bases'),
                      ),
                    ),
                  ],
                )
              : ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),
                  children: [
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        color: AppColors.secondary,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Row(
                        children: [
                          const Icon(
                            Icons.notifications_active_outlined,
                            color: AppColors.primary,
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              '${oportunidades.length} nova${oportunidades.length == 1 ? '' : 's'} oportunidade${oportunidades.length == 1 ? '' : 's'} aguardando resposta',
                              style: const TextStyle(
                                fontWeight: FontWeight.w700,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),
                    ...oportunidades.map(
                      (item) => _OportunidadeCard(oportunidade: item),
                    ),
                  ],
                ),
        ),
      ),
      bottomNavigationBar: const CompanyNavigation(selectedIndex: 4),
    );
  }
}

class _OportunidadeCard extends ConsumerStatefulWidget {
  const _OportunidadeCard({required this.oportunidade});

  final OportunidadeData oportunidade;

  @override
  ConsumerState<_OportunidadeCard> createState() => _OportunidadeCardState();
}

class _OportunidadeCardState extends ConsumerState<_OportunidadeCard> {
  bool _processando = false;

  @override
  Widget build(BuildContext context) {
    final item = widget.oportunidade;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 5,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.secondary,
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: const Text(
                    'Nova oportunidade',
                    style: TextStyle(
                      color: AppColors.primary,
                      fontWeight: FontWeight.w700,
                      fontSize: 12,
                    ),
                  ),
                ),
                const Spacer(),
                const Icon(Icons.route_outlined, size: 18),
                const SizedBox(width: 5),
                Text(
                  '${AppFormatters.numero(item.distanciaKm)} km',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Text(
              item.categorias.isEmpty
                  ? 'Eletrônicos'
                  : item.categorias.map(_capitalizar).join(', '),
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            _InfoLinha(
              icon: Icons.scale_outlined,
              label: 'Peso estimado',
              value: '${AppFormatters.numero(item.pesoEstimadoKg)} kg',
            ),
            _InfoLinha(
              icon: Icons.schedule_outlined,
              label: 'Janela solicitada',
              value: AppFormatters.dataHoraTexto(item.agendadaPara),
            ),
            _InfoLinha(
              icon: Icons.timer_outlined,
              label: 'Responder até',
              value: AppFormatters.dataHoraTexto(item.expiraEm),
              destaque: true,
            ),
            _InfoLinha(
              icon: Icons.warehouse_outlined,
              label: 'Base indicada',
              value: item.baseNome,
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                border: Border.all(color: AppColors.border),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Text(
                'O endereço e o contato serão liberados somente após o aceite.',
                style: TextStyle(color: AppColors.textLight, fontSize: 12),
              ),
            ),
            const SizedBox(height: 14),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _processando ? null : _recusar,
                    child: const Text('Recusar'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _processando ? null : _aceitar,
                    child: _processando
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('Aceitar coleta'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _aceitar() async {
    setState(() => _processando = true);
    try {
      final aceite = await ref
          .read(companyRepositoryProvider)
          .aceitarOportunidade(widget.oportunidade.id);
      ref.invalidate(oportunidadesEmpresaProvider);
      ref.invalidate(dashboardControllerProvider);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Coleta aceita'),
          content: Text(
            'Contato: ${aceite.nomeContato}\n'
            'Endereço: ${aceite.endereco}\n'
            'Agendamento: ${AppFormatters.dataHoraTexto(aceite.dataAgendamento)}',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Fechar'),
            ),
            ElevatedButton(
              onPressed: () {
                Navigator.pop(context);
                context.push('/solicitacoes/${aceite.solicitacaoId}');
              },
              child: const Text('Ver solicitação'),
            ),
          ],
        ),
      );
    } catch (error) {
      _mensagemErro(error);
      ref.invalidate(oportunidadesEmpresaProvider);
    } finally {
      if (mounted) setState(() => _processando = false);
    }
  }

  Future<void> _recusar() async {
    final controller = TextEditingController();
    final confirmar = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Recusar oportunidade'),
        content: TextField(
          controller: controller,
          maxLines: 3,
          decoration: const InputDecoration(labelText: 'Motivo (opcional)'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirmar recusa'),
          ),
        ],
      ),
    );
    final motivo = controller.text.trim();
    controller.dispose();
    if (confirmar != true || !mounted) return;
    setState(() => _processando = true);
    try {
      await ref
          .read(companyRepositoryProvider)
          .recusarOportunidade(widget.oportunidade.id, motivo: motivo);
      ref.invalidate(oportunidadesEmpresaProvider);
    } catch (error) {
      _mensagemErro(error);
    } finally {
      if (mounted) setState(() => _processando = false);
    }
  }

  void _mensagemErro(Object error) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          error is ApiException
              ? error.mensagem
              : 'Não foi possível concluir a operação.',
        ),
        backgroundColor: AppColors.error,
      ),
    );
  }

  static String _capitalizar(String valor) =>
      valor.isEmpty ? valor : '${valor[0].toUpperCase()}${valor.substring(1)}';
}

class _InfoLinha extends StatelessWidget {
  const _InfoLinha({
    required this.icon,
    required this.label,
    required this.value,
    this.destaque = false,
  });

  final IconData icon;
  final String label;
  final String value;
  final bool destaque;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 9),
    child: Row(
      children: [
        Icon(icon, size: 18, color: AppColors.textLight),
        const SizedBox(width: 8),
        Expanded(child: Text(label)),
        Text(
          value,
          textAlign: TextAlign.right,
          style: TextStyle(
            fontWeight: FontWeight.w600,
            color: destaque ? AppColors.error : null,
          ),
        ),
      ],
    ),
  );
}
