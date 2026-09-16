import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/dashboard/dashboard_data.dart';
import '../../shared/widgets/dashboard_widgets.dart';
import '../citizen/widgets/citizen_navigation.dart';
import '../company/widgets/company_navigation.dart';
import '../communication/widgets/communication_actions.dart';
import 'dashboard_controller.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final estado = ref.watch(dashboardControllerProvider);
    return Scaffold(
      appBar: AppBar(
        title: Image.asset('assets/images/ecotech navbar.png', height: 34),
        actions: [
          const CommunicationActions(),
          IconButton(
            tooltip: 'Perfil',
            onPressed: () => context.go('/perfil'),
            icon: const Icon(Icons.account_circle_outlined),
          ),
        ],
      ),
      body: estado.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (erro, _) => _ErroDashboard(
          onRetry: () =>
              ref.read(dashboardControllerProvider.notifier).recarregar(),
        ),
        data: (dados) => RefreshIndicator(
          onRefresh: () =>
              ref.read(dashboardControllerProvider.notifier).recarregar(),
          child: _ConteudoDashboard(dados: dados),
        ),
      ),
      bottomNavigationBar: switch (estado.valueOrNull?.tipo) {
        'cidadao' => const CitizenNavigation(selectedIndex: 0),
        'empresa' => const CompanyNavigation(selectedIndex: 0),
        _ => NavigationBar(
          selectedIndex: 0,
          onDestinationSelected: (indice) {
            if (indice == 1) context.go('/perfil');
          },
          destinations: const [
            NavigationDestination(
              icon: Icon(Icons.home_outlined),
              label: 'Início',
            ),
            NavigationDestination(
              icon: Icon(Icons.person_outline),
              label: 'Perfil',
            ),
          ],
        ),
      },
    );
  }
}

class _ConteudoDashboard extends StatelessWidget {
  const _ConteudoDashboard({required this.dados});

  final DashboardData dados;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final largura = math.min(constraints.maxWidth, 1100.0);
        return ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(16, 22, 16, 32),
          children: [
            Center(
              child: SizedBox(
                width: largura,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Olá, ${dados.usuario.nome.split(' ').first}!',
                      style: Theme.of(context).textTheme.titleLarge
                          ?.copyWith(fontSize: 30),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      _subtitulo(dados),
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                    const SizedBox(height: 22),
                    if (dados.tipo == 'cidadao') _DashboardCidadao(dados),
                    if (dados.tipo == 'empresa') _DashboardEmpresa(dados),
                    if (dados.tipo == 'administrador') _DashboardAdmin(dados),
                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }

  String _subtitulo(DashboardData dados) {
    if (dados.tipo == 'empresa') {
      return 'Acompanhe o desempenho e o impacto da sua empresa.';
    }
    if (dados.tipo == 'administrador') {
      return 'Visão geral da operação EcoTech.';
    }
    return 'Acompanhe seus descartes, pontos e recompensas.';
  }
}

class _DashboardCidadao extends StatelessWidget {
  const _DashboardCidadao(this.dados);

  final DashboardData dados;

  @override
  Widget build(BuildContext context) {
    final m = dados.metricas;
    final missao = dados.missao ?? const {};
    final tier = dados.proximoTier ?? const {};
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            onPressed: () => context.go('/solicitacoes/nova'),
            icon: const Icon(Icons.add_circle_outline),
            label: const Text('Solicitar descarte'),
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => context.go('/solicitacoes'),
                icon: const Icon(Icons.inventory_2_outlined),
                label: const Text('Solicitações'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => context.go('/entregas'),
                icon: const Icon(Icons.receipt_long_outlined),
                label: const Text('Entregas'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => context.go('/carteira'),
            icon: const Icon(Icons.account_balance_wallet_outlined),
            label: const Text('Carteira e saques'),
          ),
        ),
        const SizedBox(height: 16),
        _MetricGrid(
          cards: [
            MetricCard(
              label: 'Saldo acumulado',
              value: AppFormatters.moeda(m['saldo']),
              asset: 'assets/images/credito.png',
            ),
            MetricCard(
              label: 'Pontos acumulados',
              value: '${m['pontos'] ?? 0} pontos',
              asset: 'assets/images/trofeu.png',
            ),
            MetricCard(
              label: 'Tier atual',
              value: '${m['tier'] ?? '-'}',
              asset: 'assets/images/estrela.png',
            ),
            MetricCard(
              label: 'Dispositivos reciclados',
              value: '${m['dispositivos'] ?? 0}',
              asset: 'assets/images/dispositivo.png',
            ),
          ],
        ),
        const SizedBox(height: 16),
        DashboardSection(
          title: 'Missão atual',
          subtitle: '${missao['titulo'] ?? 'Recicle seus aparelhos'}',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              LinearProgressIndicator(
                value: _progresso(missao['atual'], missao['meta']),
                minHeight: 9,
                borderRadius: BorderRadius.circular(10),
              ),
              const SizedBox(height: 9),
              Text(
                '${missao['atual'] ?? 0} / ${missao['meta'] ?? 0} aparelhos',
              ),
              const SizedBox(height: 4),
              Text(
                '+${missao['recompensa_pontos'] ?? 0} pontos',
                style: const TextStyle(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        DashboardSection(
          title: 'Próxima recompensa',
          subtitle: tier['nome'] == '-'
              ? 'Você chegou ao tier máximo'
              : 'Tier ${tier['nome'] ?? '-'}',
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              LinearProgressIndicator(
                value:
                    ((tier['progresso_percentual'] as num?)?.toDouble() ?? 0) /
                    100,
                minHeight: 9,
                borderRadius: BorderRadius.circular(10),
              ),
              const SizedBox(height: 9),
              Text('${m['pontos'] ?? 0} / ${tier['meta'] ?? '-'} pontos'),
            ],
          ),
        ),
        const SizedBox(height: 16),
        DashboardSection(
          title: 'Solicitações ativas',
          child: dados.solicitacoesAtivas.isEmpty
              ? const EmptySection('Você não possui solicitações ativas.')
              : Column(
                  children: dados.solicitacoesAtivas
                      .map(_SolicitacaoTile.new)
                      .toList(),
                ),
        ),
        const SizedBox(height: 16),
        DashboardSection(
          title: 'Últimas entregas',
          child: dados.entregas.isEmpty
              ? const EmptySection('Você ainda não tem entregas no histórico.')
              : Column(children: dados.entregas.map(_EntregaTile.new).toList()),
        ),
      ],
    );
  }

  double _progresso(dynamic atual, dynamic meta) {
    final a = (atual as num?)?.toDouble() ?? 0;
    final m = (meta as num?)?.toDouble() ?? 1;
    return (a / m).clamp(0, 1).toDouble();
  }
}

class _DashboardEmpresa extends StatelessWidget {
  const _DashboardEmpresa(this.dados);

  final DashboardData dados;

  @override
  Widget build(BuildContext context) {
    final m = dados.metricas;
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () => context.go('/empresa/oportunidades'),
                icon: const Icon(Icons.campaign_outlined),
                label: const Text('Oportunidades'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => context.go('/empresa/operacoes'),
                icon: const Icon(Icons.inventory_2_outlined),
                label: const Text('Operacoes'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => context.go('/relatorios'),
            icon: const Icon(Icons.bar_chart_outlined),
            label: const Text('Relatórios ambientais'),
          ),
        ),
        const SizedBox(height: 16),
        _MetricGrid(
          cards: [
            MetricCard(
              label: 'Finalizadas',
              value: '${m['finalizadas'] ?? 0}',
              asset: 'assets/images/trofeu.png',
            ),
            MetricCard(
              label: 'Operações ativas',
              value: '${m['ativas'] ?? 0}',
              asset: 'assets/images/planta.png',
            ),
            MetricCard(
              label: 'Peso processado',
              value: '${AppFormatters.numero(m['peso_processado_kg'])} kg',
              asset: 'assets/images/dispositivo.png',
            ),
            MetricCard(
              label: 'Receita recebida',
              value: AppFormatters.moeda(m['saldo']),
              asset: 'assets/images/notif-dinheiro.png',
            ),
          ],
        ),
        const SizedBox(height: 16),
        DashboardSection(
          title: 'Desempenho e impacto',
          subtitle: dados.comparativoMensal == null
              ? 'Comparativo disponível após dois meses com movimentação.'
              : '${dados.comparativoMensal! >= 0 ? '+' : ''}${AppFormatters.numero(dados.comparativoMensal)}% comparado ao mês anterior',
          child: _GraficoMeses(dados.meses),
        ),
        const SizedBox(height: 16),
        DashboardSection(
          title: 'Impacto acumulado',
          child: Column(
            children: [
              _ResumoImpacto(metricas: m),
              if (dados.categorias.isNotEmpty) ...[
                const SizedBox(height: 20),
                _Categorias(categorias: dados.categorias),
              ],
            ],
          ),
        ),
        const SizedBox(height: 16),
        DashboardSection(
          title: 'Solicitações em processamento',
          subtitle: '${dados.totalEmProcessamento} no total',
          child: dados.emProcessamento.isEmpty
              ? const EmptySection(
                  'Sua empresa não possui solicitações em processamento.',
                )
              : Column(
                  children: dados.emProcessamento
                      .map(_SolicitacaoTile.new)
                      .toList(),
                ),
        ),
      ],
    );
  }
}

class _DashboardAdmin extends StatelessWidget {
  const _DashboardAdmin(this.dados);

  final DashboardData dados;

  @override
  Widget build(BuildContext context) {
    final m = dados.metricas;
    return Column(
      children: [
        SizedBox(
          width: double.infinity,
          child: OutlinedButton.icon(
            onPressed: () => context.go('/relatorios'),
            icon: const Icon(Icons.bar_chart_outlined),
            label: const Text('Relatórios do sistema'),
          ),
        ),
        const SizedBox(height: 16),
        _MetricGrid(
          cards: [
            MetricCard(
              label: 'Total processado',
              value: '${AppFormatters.numero(m['peso_total_kg'])} kg',
              asset: 'assets/images/credito.png',
            ),
            MetricCard(
              label: 'Solicitações',
              value: '${m['solicitacoes'] ?? 0}',
              asset: 'assets/images/trofeu.png',
            ),
            MetricCard(
              label: 'Impacto evitado',
              value: '${AppFormatters.numero(m['impacto_evitado_kg'])} kg CO₂',
              asset: 'assets/images/planta.png',
            ),
            MetricCard(
              label: 'Receita EcoTech',
              value: AppFormatters.moeda(m['receita']),
              asset: 'assets/images/notif-dinheiro.png',
            ),
          ],
        ),
        const SizedBox(height: 16),
        DashboardSection(
          title: 'Últimas solicitações do sistema',
          subtitle: '${m['ativas'] ?? 0} solicitações ativas',
          child: dados.solicitacoesRecentes.isEmpty
              ? const EmptySection('Nenhuma solicitação cadastrada.')
              : Column(
                  children: dados.solicitacoesRecentes
                      .map(_SolicitacaoTile.new)
                      .toList(),
                ),
        ),
      ],
    );
  }
}

class _MetricGrid extends StatelessWidget {
  const _MetricGrid({required this.cards});

  final List<Widget> cards;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
    builder: (context, constraints) {
      final colunas = constraints.maxWidth >= 800 ? 4 : 2;
      final largura = (constraints.maxWidth - (colunas - 1) * 12) / colunas;
      return Wrap(
        spacing: 12,
        runSpacing: 12,
        children: cards
            .map((card) => SizedBox(width: largura, height: 132, child: card))
            .toList(),
      );
    },
  );
}

class _GraficoMeses extends StatelessWidget {
  const _GraficoMeses(this.meses);

  final List<MesDashboard> meses;

  @override
  Widget build(BuildContext context) {
    final maior = meses.fold<double>(
      0,
      (valor, item) => math.max(valor, item.pesoKg),
    );
    return SizedBox(
      height: 190,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: meses.map((mes) {
          final altura = maior == 0 ? 2.0 : 110 * mes.pesoKg / maior;
          return Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 3),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Text(
                    '${AppFormatters.numero(mes.pesoKg)} kg',
                    style: const TextStyle(fontSize: 10),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 5),
                  Container(
                    height: math.max(altura, 2),
                    decoration: BoxDecoration(
                      color: AppColors.primaryLight,
                      borderRadius: const BorderRadius.vertical(
                        top: Radius.circular(6),
                      ),
                    ),
                  ),
                  const SizedBox(height: 7),
                  Text(mes.mes, style: const TextStyle(fontSize: 11)),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _ResumoImpacto extends StatelessWidget {
  const _ResumoImpacto({required this.metricas});

  final Map<String, dynamic> metricas;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Expanded(
        child: _ImpactoItem(
          '${AppFormatters.numero(metricas['co2_evitado_kg'])} kg',
          'CO₂ evitado',
        ),
      ),
      const SizedBox(width: 8),
      Expanded(
        child: _ImpactoItem(
          '${AppFormatters.numero(metricas['taxa_reciclagem_percentual'])}%',
          'Taxa de reciclagem',
        ),
      ),
      const SizedBox(width: 8),
      Expanded(
        child: _ImpactoItem(
          '${AppFormatters.numero(metricas['peso_processado_kg'])} kg',
          'Peso processado',
        ),
      ),
    ],
  );
}

class _ImpactoItem extends StatelessWidget {
  const _ImpactoItem(this.valor, this.rotulo);
  final String valor;
  final String rotulo;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(10),
    decoration: BoxDecoration(
      color: AppColors.secondary,
      borderRadius: BorderRadius.circular(10),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(valor, style: const TextStyle(fontWeight: FontWeight.w700)),
        const SizedBox(height: 4),
        Text(
          rotulo,
          style: const TextStyle(fontSize: 11, color: AppColors.textLight),
        ),
      ],
    ),
  );
}

class _Categorias extends StatelessWidget {
  const _Categorias({required this.categorias});
  final List<CategoriaDashboard> categorias;
  @override
  Widget build(BuildContext context) {
    final maior = categorias.fold<double>(
      0,
      (valor, item) => math.max(valor, item.pesoKg),
    );
    return Column(
      children: categorias
          .map(
            (categoria) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          categoria.nome,
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),
                      ),
                      Text('${AppFormatters.numero(categoria.pesoKg)} kg'),
                    ],
                  ),
                  const SizedBox(height: 5),
                  LinearProgressIndicator(
                    value: maior == 0 ? 0 : categoria.pesoKg / maior,
                    minHeight: 7,
                    borderRadius: BorderRadius.circular(8),
                  ),
                ],
              ),
            ),
          )
          .toList(),
    );
  }
}

class _SolicitacaoTile extends StatelessWidget {
  const _SolicitacaoTile(this.solicitacao);
  final SolicitacaoResumo solicitacao;
  @override
  Widget build(BuildContext context) => ListTile(
    contentPadding: EdgeInsets.zero,
    leading: CircleAvatar(
      backgroundColor: AppColors.secondary,
      child: Image.asset('assets/images/pacote.png', width: 25),
    ),
    title: Text(
      'Solicitação #${solicitacao.id.substring(0, math.min(8, solicitacao.id.length))}',
    ),
    subtitle: Text(
      '${solicitacao.cidadao} · ${AppFormatters.numero(solicitacao.pesoKg, casas: 2)} kg\n${AppFormatters.data(solicitacao.dataCriacao)}',
    ),
    isThreeLine: true,
    trailing: StatusBadge(solicitacao.estado),
  );
}

class _EntregaTile extends StatelessWidget {
  const _EntregaTile(this.entrega);
  final EntregaResumo entrega;
  @override
  Widget build(BuildContext context) => ListTile(
    contentPadding: EdgeInsets.zero,
    leading: CircleAvatar(
      backgroundColor: AppColors.secondary,
      child: Image.asset('assets/images/pacote.png', width: 25),
    ),
    title: const Text('Incentivo por coleta'),
    subtitle: Text(
      '${entrega.empresa}\n${AppFormatters.dataTexto(entrega.data)}',
    ),
    isThreeLine: true,
    trailing: Text(
      AppFormatters.moeda(entrega.valor),
      style: const TextStyle(fontWeight: FontWeight.w700),
    ),
  );
}

class _ErroDashboard extends StatelessWidget {
  const _ErroDashboard({required this.onRetry});
  final VoidCallback onRetry;
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.cloud_off_outlined,
            size: 44,
            color: AppColors.textLight,
          ),
          const SizedBox(height: 12),
          const Text('Não foi possível carregar o dashboard.'),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: onRetry,
            child: const Text('Tentar novamente'),
          ),
        ],
      ),
    ),
  );
}
