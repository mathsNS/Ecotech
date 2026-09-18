import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/company/company_data.dart';
import 'company_controller.dart';
import 'widgets/company_navigation.dart';
import 'widgets/company_states.dart';
import 'widgets/operational_form.dart';

class PontosEmpresaScreen extends ConsumerWidget {
  const PontosEmpresaScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(pontosEmpresaProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Pontos de coleta')),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(pontosEmpresaProvider),
        ),
        data: (pontos) => RefreshIndicator(
          onRefresh: () => ref.refresh(pontosEmpresaProvider.future),
          child: pontos.isEmpty
              ? ListView(
                  children: [
                    const SizedBox(height: 110),
                    CompanyEmpty(
                      message: 'Sua empresa ainda não possui pontos de coleta.',
                      action: ElevatedButton.icon(
                        onPressed: () => _abrirFormulario(context, ref),
                        icon: const Icon(Icons.add),
                        label: const Text('Cadastrar ponto'),
                      ),
                    ),
                  ],
                )
              : ListView.builder(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 90),
                  itemCount: pontos.length,
                  itemBuilder: (context, index) => _PontoCard(pontos[index]),
                ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _abrirFormulario(context, ref),
        icon: const Icon(Icons.add),
        label: const Text('Novo ponto'),
      ),
      bottomNavigationBar: const CompanyNavigation(selectedIndex: 4),
    );
  }

  static Future<void> _abrirFormulario(
    BuildContext context,
    WidgetRef ref, [
    PontoEmpresaData? ponto,
  ]) async {
    final saved = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (context) => OperationalForm(
          title: ponto == null ? 'Novo ponto de coleta' : 'Editar ponto',
          initialName: ponto?.nome ?? '',
          currentAddress: ponto?.endereco,
          initialCapacity: ponto?.capacidadeKg ?? 1000,
          onSave: (data) => ref
              .read(companyRepositoryProvider)
              .salvarPonto(data, id: ponto?.id),
        ),
      ),
    );
    if (saved == true) ref.invalidate(pontosEmpresaProvider);
  }
}

class _PontoCard extends ConsumerWidget {
  const _PontoCard(this.ponto);

  final PontoEmpresaData ponto;

  @override
  Widget build(BuildContext context, WidgetRef ref) => Card(
    margin: const EdgeInsets.only(bottom: 14),
    child: Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  ponto.nome,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
              Switch(
                value: ponto.ativa,
                onChanged: (value) => _atividade(context, ref, value),
              ),
            ],
          ),
          Text(ponto.endereco),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: LinearProgressIndicator(
                  value: ponto.ocupacaoPercentual,
                  minHeight: 8,
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              const SizedBox(width: 10),
              Text(
                '${AppFormatters.numero(ponto.ocupacaoKg)} / '
                '${AppFormatters.numero(ponto.capacidadeKg)} kg',
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              OutlinedButton.icon(
                onPressed: () =>
                    PontosEmpresaScreen._abrirFormulario(context, ref, ponto),
                icon: const Icon(Icons.edit_outlined),
                label: const Text('Editar'),
              ),
              const Spacer(),
              Text(
                '${ponto.solicitacoes.length} entrega${ponto.solicitacoes.length == 1 ? '' : 's'}',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ],
          ),
          const Divider(height: 26),
          ExpansionTile(
            tilePadding: EdgeInsets.zero,
            childrenPadding: EdgeInsets.zero,
            title: const Text('Entregas associadas'),
            children: ponto.solicitacoes.isEmpty
                ? const [
                    Padding(
                      padding: EdgeInsets.only(bottom: 12),
                      child: Text('Nenhuma entrega associada a este ponto.'),
                    ),
                  ]
                : ponto.solicitacoes
                      .map(
                        (entrega) =>
                            _EntregaTile(pontoId: ponto.id, entrega: entrega),
                      )
                      .toList(),
          ),
        ],
      ),
    ),
  );

  Future<void> _atividade(
    BuildContext context,
    WidgetRef ref,
    bool ativa,
  ) async {
    try {
      await ref
          .read(companyRepositoryProvider)
          .definirAtividadePonto(ponto.id, ativa);
      ref.invalidate(pontosEmpresaProvider);
    } catch (error) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            error is ApiException
                ? error.mensagem
                : 'Não foi possível alterar.',
          ),
          backgroundColor: AppColors.error,
        ),
      );
    }
  }
}

class _EntregaTile extends ConsumerWidget {
  const _EntregaTile({required this.pontoId, required this.entrega});

  final String pontoId;
  final EntregaPontoData entrega;

  @override
  Widget build(BuildContext context, WidgetRef ref) => ListTile(
    contentPadding: EdgeInsets.zero,
    onTap: () => context.push('/solicitacoes/${entrega.id}'),
    title: Text(entrega.cidadao),
    subtitle: Text(
      '${AppFormatters.dataHoraTexto(entrega.dataAgendamento ?? '')}\n'
      '${AppFormatters.numero(entrega.pesoKg, casas: 2)} kg · ${entrega.estado}',
    ),
    isThreeLine: true,
    trailing: entrega.podeConfirmar
        ? ElevatedButton(
            onPressed: () => _confirmar(context, ref),
            child: const Text('Receber'),
          )
        : Icon(
            entrega.confirmadoEmpresa
                ? Icons.check_circle_outline
                : Icons.chevron_right,
            color: entrega.confirmadoEmpresa ? AppColors.success : null,
          ),
  );

  Future<void> _confirmar(BuildContext context, WidgetRef ref) async {
    final controller = TextEditingController(
      text: entrega.pesoKg.toStringAsFixed(2),
    );
    final peso = await showDialog<double>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Confirmar recebimento'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              entrega.pesoInformadoCidadao
                  ? 'Confira o peso informado pelo cidadão na balança da empresa.'
                  : 'O cidadão não informou o peso. Faça a pesagem antes de confirmar.',
            ),
            const SizedBox(height: 14),
            TextField(
              controller: controller,
              autofocus: true,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: const InputDecoration(labelText: 'Peso aferido (kg)'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              final valor = double.tryParse(
                controller.text.replaceAll(',', '.'),
              );
              if (valor != null && valor > 0) Navigator.pop(context, valor);
            },
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (peso == null || !context.mounted) return;
    try {
      await ref
          .read(companyRepositoryProvider)
          .confirmarEntrega(pontoId, entrega.id, peso);
      ref.invalidate(pontosEmpresaProvider);
      if (!context.mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Recebimento confirmado.')));
    } catch (error) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            error is ApiException
                ? error.mensagem
                : 'Não foi possível confirmar o recebimento.',
          ),
          backgroundColor: AppColors.error,
        ),
      );
    }
  }
}
