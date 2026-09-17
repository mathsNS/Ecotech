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

class PrecosAdminScreen extends ConsumerWidget {
  const PrecosAdminScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(precosAdminProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tabela de preços'),
        actions: const [CommunicationActions()],
      ),
      bottomNavigationBar: const AdminNavigation(selectedIndex: 4),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(precosAdminProvider),
        ),
        data: (precos) {
          final categorias = <String, List<PrecoAdminData>>{};
          for (final preco in precos) {
            categorias.putIfAbsent(preco.categoria, () => []).add(preco);
          }
          return RefreshIndicator(
            onRefresh: () => ref.refresh(precosAdminProvider.future),
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 30),
              children: [
                const _LegendaPrecos(),
                const SizedBox(height: 14),
                for (final categoria in categorias.entries) ...[
                  Text(_rotulo(categoria.key), style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 7),
                  ...categoria.value.map(
                    (preco) => _PrecoCard(
                      preco,
                      onEditar: () => _editar(context, ref, preco),
                    ),
                  ),
                  const SizedBox(height: 12),
                ],
              ],
            ),
          );
        },
      ),
    );
  }

  Future<void> _editar(
    BuildContext context,
    WidgetRef ref,
    PrecoAdminData preco,
  ) async {
    final valores = await showDialog<({double base, double minimo})>(
      context: context,
      builder: (_) => _EditarPrecoDialog(preco),
    );
    if (valores == null || !context.mounted) return;
    try {
      await ref.read(adminRepositoryProvider).atualizarPreco(
        subcategoria: preco.subcategoria,
        valorBase: valores.base,
        valorMinimo: valores.minimo,
      );
      ref.invalidate(precosAdminProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Preço atualizado com sucesso.')),
        );
      }
    } catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(error is ApiException ? error.mensagem : 'Não foi possível atualizar o preço.')),
        );
      }
    }
  }
}

class _LegendaPrecos extends StatelessWidget {
  const _LegendaPrecos();
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
            'Funcionando usa 100% do valor base; defeito leve 40%; defeito grave 15%; sucata usa o valor mínimo. Propostas acima de 150% exigem aprovação.',
          ),
        ),
      ],
    ),
  );
}

class _PrecoCard extends StatelessWidget {
  const _PrecoCard(this.preco, {required this.onEditar});
  final PrecoAdminData preco;
  final VoidCallback onEditar;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 8),
    child: Padding(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(child: Text(_rotulo(preco.subcategoria), style: const TextStyle(fontWeight: FontWeight.w700))),
              IconButton(tooltip: 'Editar', onPressed: onEditar, icon: const Icon(Icons.edit_outlined)),
            ],
          ),
          Row(
            children: [
              Expanded(child: _Valor('Funcionando', preco.valorBase)),
              const SizedBox(width: 8),
              Expanded(child: _Valor('Sucata', preco.valorMinimo)),
              const SizedBox(width: 8),
              Expanded(child: _Valor('Limite', preco.limiteOverride)),
            ],
          ),
        ],
      ),
    ),
  );
}

class _Valor extends StatelessWidget {
  const _Valor(this.rotulo, this.valor);
  final String rotulo;
  final double valor;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(9),
    decoration: BoxDecoration(
      color: AppColors.backgroundAlt,
      borderRadius: BorderRadius.circular(9),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(AppFormatters.moeda(valor), maxLines: 1, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
        Text(rotulo, style: const TextStyle(fontSize: 9, color: AppColors.textLight)),
      ],
    ),
  );
}

class _EditarPrecoDialog extends StatefulWidget {
  const _EditarPrecoDialog(this.preco);
  final PrecoAdminData preco;
  @override
  State<_EditarPrecoDialog> createState() => _EditarPrecoDialogState();
}

class _EditarPrecoDialogState extends State<_EditarPrecoDialog> {
  final _form = GlobalKey<FormState>();
  late final TextEditingController _base;
  late final TextEditingController _minimo;

  @override
  void initState() {
    super.initState();
    _base = TextEditingController(text: widget.preco.valorBase.toStringAsFixed(2).replaceAll('.', ','));
    _minimo = TextEditingController(text: widget.preco.valorMinimo.toStringAsFixed(2).replaceAll('.', ','));
  }

  @override
  void dispose() {
    _base.dispose();
    _minimo.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: Text('Editar ${_rotulo(widget.preco.subcategoria)}'),
    content: Form(
      key: _form,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextFormField(
            controller: _base,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(labelText: 'Valor base', prefixText: 'R\$ '),
            validator: (value) => (_numero(value) ?? 0) <= 0 ? 'Informe um valor positivo.' : null,
          ),
          const SizedBox(height: 12),
          TextFormField(
            controller: _minimo,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(labelText: 'Valor mínimo de sucata', prefixText: 'R\$ '),
            validator: (value) {
              final minimo = _numero(value);
              final base = _numero(_base.text);
              if (minimo == null || minimo < 0) return 'Informe um valor válido.';
              if (base != null && minimo >= base) return 'O mínimo deve ser menor que o valor base.';
              return null;
            },
          ),
        ],
      ),
    ),
    actions: [
      TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
      ElevatedButton(
        onPressed: () {
          if (!_form.currentState!.validate()) return;
          Navigator.pop(context, (base: _numero(_base.text)!, minimo: _numero(_minimo.text)!));
        },
        child: const Text('Salvar'),
      ),
    ],
  );

  static double? _numero(String? valor) =>
      double.tryParse((valor ?? '').replaceAll(',', '.'));
}

String _rotulo(String valor) {
  final texto = valor.replaceAll('_', ' ');
  return texto.isEmpty ? texto : '${texto[0].toUpperCase()}${texto.substring(1)}';
}
