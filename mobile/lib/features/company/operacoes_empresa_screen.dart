import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/company/operation_data.dart';
import '../../shared/widgets/dashboard_widgets.dart';
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
  final _buscaController = TextEditingController();
  String _estado = '';
  String _busca = '';
  int _pagina = 1;

  OperacoesConsulta get _consulta =>
      (estado: _estado, busca: _busca, pagina: _pagina);

  @override
  void dispose() {
    _buscaController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(operacoesEmpresaProvider(_consulta));
    return Scaffold(
      appBar: AppBar(title: const Text('Operacoes')),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(operacoesEmpresaProvider(_consulta)),
        ),
        data: (dados) => RefreshIndicator(
          onRefresh: () =>
              ref.refresh(operacoesEmpresaProvider(_consulta).future),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
            children: [
              _Filtros(
                controller: _buscaController,
                estado: _estado,
                onBuscar: () => setState(() {
                  _busca = _buscaController.text.trim();
                  _pagina = 1;
                }),
                onEstado: (value) => setState(() {
                  _estado = value ?? '';
                  _pagina = 1;
                }),
              ),
              const SizedBox(height: 14),
              _Estatisticas(dados),
              const SizedBox(height: 14),
              if (dados.operacoes.isEmpty)
                const CompanyEmpty(
                  message: 'Nenhuma operacao encontrada para estes filtros.',
                )
              else
                ...dados.operacoes.map((item) => _OperacaoCard(operacao: item)),
              if (dados.totalPaginas > 1)
                _Paginacao(
                  pagina: dados.pagina,
                  totalPaginas: dados.totalPaginas,
                  onAnterior: dados.pagina > 1
                      ? () => setState(() => _pagina--)
                      : null,
                  onProxima: dados.pagina < dados.totalPaginas
                      ? () => setState(() => _pagina++)
                      : null,
                ),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const CompanyNavigation(selectedIndex: 2),
    );
  }
}

class _Filtros extends StatelessWidget {
  const _Filtros({
    required this.controller,
    required this.estado,
    required this.onBuscar,
    required this.onEstado,
  });

  final TextEditingController controller;
  final String estado;
  final VoidCallback onBuscar;
  final ValueChanged<String?> onEstado;

  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    child: Padding(
      padding: const EdgeInsets.all(14),
      child: Column(
        children: [
          TextField(
            controller: controller,
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => onBuscar(),
            decoration: InputDecoration(
              labelText: 'Buscar por cliente ou codigo',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: IconButton(
                onPressed: onBuscar,
                icon: const Icon(Icons.arrow_forward),
                tooltip: 'Buscar',
              ),
            ),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: estado,
            decoration: const InputDecoration(labelText: 'Estado'),
            items: const [
              DropdownMenuItem(value: '', child: Text('Todos os estados')),
              DropdownMenuItem(value: 'Solicitado', child: Text('Solicitado')),
              DropdownMenuItem(value: 'Coletado', child: Text('Coletado')),
              DropdownMenuItem(
                value: 'Em Processamento',
                child: Text('Em processamento'),
              ),
              DropdownMenuItem(value: 'Reciclado', child: Text('Reciclado')),
              DropdownMenuItem(
                value: 'Reutilizado',
                child: Text('Reutilizado'),
              ),
              DropdownMenuItem(value: 'Descartado', child: Text('Descartado')),
              DropdownMenuItem(value: 'Cancelado', child: Text('Cancelado')),
            ],
            onChanged: onEstado,
          ),
        ],
      ),
    ),
  );
}

class _Estatisticas extends StatelessWidget {
  const _Estatisticas(this.dados);
  final OperacoesPaginaData dados;

  @override
  Widget build(BuildContext context) => SizedBox(
    height: 72,
    child: ListView(
      scrollDirection: Axis.horizontal,
      children: [
        _Indicador(label: 'Visiveis', valor: dados.total),
        ...dados.estatisticas.entries
            .where((entry) => entry.value > 0)
            .map((entry) => _Indicador(label: entry.key, valor: entry.value)),
      ],
    ),
  );
}

class _Indicador extends StatelessWidget {
  const _Indicador({required this.label, required this.valor});
  final String label;
  final int valor;

  @override
  Widget build(BuildContext context) => Container(
    width: 126,
    margin: const EdgeInsets.only(right: 9),
    padding: const EdgeInsets.all(11),
    decoration: BoxDecoration(
      color: AppColors.secondary,
      borderRadius: BorderRadius.circular(12),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('$valor', style: Theme.of(context).textTheme.titleMedium),
        Text(
          label,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontSize: 11, color: AppColors.textLight),
        ),
      ],
    ),
  );
}

class _OperacaoCard extends StatelessWidget {
  const _OperacaoCard({required this.operacao});
  final OperacaoResumoData operacao;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 12),
    child: InkWell(
      borderRadius: BorderRadius.circular(12),
      onTap: () => context.push('/empresa/operacoes/${operacao.id}'),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    operacao.cidadao,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                StatusBadge(operacao.estado),
              ],
            ),
            const SizedBox(height: 5),
            Text(
              '#${operacao.id.substring(0, 8)}  |  '
              '${AppFormatters.data(operacao.dataCriacao)}',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const Divider(height: 24),
            Row(
              children: [
                const Icon(Icons.devices_other_outlined, size: 19),
                const SizedBox(width: 7),
                Text('${operacao.quantidadeItens} item(ns)'),
                const Spacer(),
                const Icon(Icons.scale_outlined, size: 19),
                const SizedBox(width: 7),
                Text(
                  '${AppFormatters.numero(operacao.pesoKg, casas: 2)} kg',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              alignment: WrapAlignment.end,
              spacing: 4,
              children: [
                TextButton.icon(
                  onPressed: () => context.push('/conversas/${operacao.id}'),
                  icon: const Icon(Icons.chat_bubble_outline),
                  label: const Text('Conversa'),
                ),
                TextButton.icon(
                  onPressed: () =>
                      context.push('/solicitacoes/${operacao.id}/agenda'),
                  icon: const Icon(Icons.calendar_month_outlined),
                  label: const Text('Agenda'),
                ),
                TextButton.icon(
                  onPressed: () =>
                      context.push('/empresa/operacoes/${operacao.id}'),
                  icon: const Icon(Icons.visibility_outlined),
                  label: const Text('Detalhes'),
                ),
              ],
            ),
          ],
        ),
      ),
    ),
  );
}

class _Paginacao extends StatelessWidget {
  const _Paginacao({
    required this.pagina,
    required this.totalPaginas,
    this.onAnterior,
    this.onProxima,
  });
  final int pagina;
  final int totalPaginas;
  final VoidCallback? onAnterior;
  final VoidCallback? onProxima;

  @override
  Widget build(BuildContext context) => Row(
    mainAxisAlignment: MainAxisAlignment.center,
    children: [
      IconButton(onPressed: onAnterior, icon: const Icon(Icons.chevron_left)),
      Text('$pagina de $totalPaginas'),
      IconButton(onPressed: onProxima, icon: const Icon(Icons.chevron_right)),
    ],
  );
}
