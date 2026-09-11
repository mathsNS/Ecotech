import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/citizen/citizen_data.dart';
import '../../shared/widgets/dashboard_widgets.dart';
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
    return Scaffold(
      appBar: AppBar(
        title: const Text('Minhas solicitações'),
        actions: [
          IconButton(
            tooltip: 'Histórico de incentivos',
            onPressed: () => context.push('/entregas'),
            icon: const Icon(Icons.account_balance_wallet_outlined),
          ),
        ],
      ),
      body: Column(
        children: [
          SizedBox(
            height: 58,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              children: [
                _Filtro('Todas', '', _estado, _selecionar),
                _Filtro('Solicitadas', 'Solicitado', _estado, _selecionar),
                _Filtro('Em coleta', 'Coletado', _estado, _selecionar),
                _Filtro(
                  'Processando',
                  'Em Processamento',
                  _estado,
                  _selecionar,
                ),
                _Filtro('Finalizadas', 'Reciclado', _estado, _selecionar),
              ],
            ),
          ),
          Expanded(
            child: state.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => CitizenError(
                error: error,
                onRetry: () => ref.invalidate(solicitacoesProvider(_estado)),
              ),
              data: (pagina) => RefreshIndicator(
                onRefresh: () =>
                    ref.refresh(solicitacoesProvider(_estado).future),
                child: pagina.itens.isEmpty
                    ? ListView(
                        children: [
                          const SizedBox(height: 100),
                          CitizenEmpty(
                            message: 'Nenhuma solicitação encontrada.',
                            action: ElevatedButton(
                              onPressed: () =>
                                  context.push('/solicitacoes/nova'),
                              child: const Text('Criar solicitação'),
                            ),
                          ),
                        ],
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                        itemCount: pagina.itens.length,
                        itemBuilder: (context, index) =>
                            _SolicitacaoCard(pagina.itens[index]),
                      ),
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.push('/solicitacoes/nova'),
        icon: const Icon(Icons.add),
        label: const Text('Nova solicitação'),
      ),
      bottomNavigationBar: const CitizenNavigation(selectedIndex: 1),
    );
  }

  void _selecionar(String estado) => setState(() => _estado = estado);
}

class _Filtro extends StatelessWidget {
  const _Filtro(this.label, this.value, this.selected, this.onSelected);
  final String label;
  final String value;
  final String selected;
  final ValueChanged<String> onSelected;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(right: 7),
    child: ChoiceChip(
      label: Text(label),
      selected: selected == value,
      onSelected: (_) => onSelected(value),
    ),
  );
}

class _SolicitacaoCard extends StatelessWidget {
  const _SolicitacaoCard(this.solicitacao);
  final SolicitacaoData solicitacao;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 12),
    child: InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () => context.push('/solicitacoes/${solicitacao.id}'),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Solicitação #${solicitacao.id.substring(0, 8)}',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                StatusBadge(solicitacao.estado),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                const Icon(
                  Icons.scale_outlined,
                  size: 18,
                  color: AppColors.textLight,
                ),
                const SizedBox(width: 6),
                Text(
                  '${AppFormatters.numero(solicitacao.pesoExibidoKg, casas: 2)} kg (${solicitacao.pesoOrigem})',
                ),
                const Spacer(),
                Text(AppFormatters.data(solicitacao.dataCriacao)),
              ],
            ),
            const SizedBox(height: 7),
            Text(
              solicitacao.empresa ??
                  solicitacao.pontoColeta ??
                  'Empresa ainda não definida',
            ),
            const SizedBox(height: 12),
            const Align(
              alignment: Alignment.centerRight,
              child: Text(
                'Ver detalhes',
                style: TextStyle(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
