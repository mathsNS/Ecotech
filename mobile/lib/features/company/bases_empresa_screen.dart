import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/company/company_data.dart';
import 'company_controller.dart';
import 'widgets/company_navigation.dart';
import 'widgets/company_states.dart';
import 'widgets/operational_form.dart';

class BasesEmpresaScreen extends ConsumerWidget {
  const BasesEmpresaScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(basesEmpresaProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Bases operacionais')),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(basesEmpresaProvider),
        ),
        data: (bases) => RefreshIndicator(
          onRefresh: () => ref.refresh(basesEmpresaProvider.future),
          child: bases.isEmpty
              ? ListView(
                  children: [
                    const SizedBox(height: 110),
                    CompanyEmpty(
                      message: 'Cadastre uma base para começar a receber oportunidades de coleta domiciliar.',
                      action: ElevatedButton.icon(
                        onPressed: () => _abrirFormulario(context, ref),
                        icon: const Icon(Icons.add),
                        label: const Text('Cadastrar base'),
                      ),
                    ),
                  ],
                )
              : ListView.builder(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 90),
                  itemCount: bases.length,
                  itemBuilder: (context, index) => _BaseCard(bases[index]),
                ),
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _abrirFormulario(context, ref),
        icon: const Icon(Icons.add),
        label: const Text('Nova base'),
      ),
      bottomNavigationBar: const CompanyNavigation(selectedIndex: 4),
    );
  }

  static Future<void> _abrirFormulario(
    BuildContext context,
    WidgetRef ref, [
    BaseEmpresaData? base,
  ]) async {
    final saved = await Navigator.push<bool>(
      context,
      MaterialPageRoute(
        builder: (context) => OperationalForm(
          title: base == null ? 'Nova base operacional' : 'Editar base',
          initialName: base?.nome ?? '',
          currentAddress: base?.endereco,
          initialCapacity: base?.capacidadeKg ?? 1000,
          initialRadius: base?.raioAtendimentoKm ?? 25,
          initialHomeCollection: base?.realizaColetaDomiciliar ?? true,
          onSave: (data) => ref
              .read(companyRepositoryProvider)
              .salvarBase(data, id: base?.id),
        ),
      ),
    );
    if (saved == true) {
      ref.invalidate(basesEmpresaProvider);
      ref.invalidate(oportunidadesEmpresaProvider);
    }
  }
}

class _BaseCard extends ConsumerWidget {
  const _BaseCard(this.base);

  final BaseEmpresaData base;

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
                  base.nome,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
                decoration: BoxDecoration(
                  color: base.ativa
                      ? AppColors.secondary
                      : AppColors.backgroundAlt,
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  base.ativa ? 'Ativa' : 'Inativa',
                  style: TextStyle(
                    color: base.ativa ? AppColors.primary : AppColors.textLight,
                    fontWeight: FontWeight.w700,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 7),
          Text(base.endereco),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _Metrica(
                  label: 'Raio',
                  value: '${AppFormatters.numero(base.raioAtendimentoKm)} km',
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _Metrica(
                  label: 'Disponível',
                  value:
                      '${AppFormatters.numero(base.capacidadeDisponivelKg)} kg',
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: _Metrica(
                  label: 'Coleta em casa',
                  value: base.realizaColetaDomiciliar ? 'Sim' : 'Não',
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () =>
                      BasesEmpresaScreen._abrirFormulario(context, ref, base),
                  icon: const Icon(Icons.edit_outlined),
                  label: const Text('Editar'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton(
                  onPressed: () => _atividade(context, ref),
                  child: Text(base.ativa ? 'Desativar' : 'Ativar'),
                ),
              ),
            ],
          ),
        ],
      ),
    ),
  );

  Future<void> _atividade(BuildContext context, WidgetRef ref) async {
    try {
      await ref
          .read(companyRepositoryProvider)
          .definirAtividadeBase(base.id, !base.ativa);
      ref.invalidate(basesEmpresaProvider);
      ref.invalidate(oportunidadesEmpresaProvider);
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

class _Metrica extends StatelessWidget {
  const _Metrica({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(
      color: AppColors.backgroundAlt,
      borderRadius: BorderRadius.circular(10),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(color: AppColors.textLight, fontSize: 11),
        ),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontWeight: FontWeight.w700)),
      ],
    ),
  );
}
