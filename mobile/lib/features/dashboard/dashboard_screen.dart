import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/dashboard/dashboard_data.dart';
import '../../shared/widgets/dashboard_widgets.dart';
import '../admin/widgets/admin_navigation.dart';
import '../citizen/widgets/citizen_navigation.dart';
import '../company/widgets/company_navigation.dart';
import '../communication/widgets/communication_actions.dart';
import 'citizen_dashboard_view.dart';
import 'company_dashboard_view.dart';
import 'dashboard_header.dart';
import 'dashboard_controller.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final estado = ref.watch(dashboardControllerProvider);
    final dadosAtuais = estado.valueOrNull;
    final empresa = dadosAtuais?.tipo == 'empresa';
    final citizen = dadosAtuais?.tipo == 'cidadao';
    return Scaffold(
      backgroundColor: empresa || citizen ? const Color(0xFFF6F7F8) : null,
      appBar: empresa || citizen
          ? EcoTechDashboardHeader(name: dadosAtuais!.usuario.nome)
          : AppBar(
              title: Image.asset(
                'assets/images/ecotech navbar.png',
                height: 34,
              ),
              actions: [
                const CommunicationActions(),
                IconButton(
                  tooltip: 'Perfil',
                  onPressed: () => context.push('/perfil'),
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
        data: (dados) => switch (dados.tipo) {
          'empresa' => CompanyDashboardView(
            data: dados,
            onRefresh: () =>
                ref.read(dashboardControllerProvider.notifier).recarregar(),
          ),
          'cidadao' => CitizenDashboardView(
            data: dados,
            onRefresh: () =>
                ref.read(dashboardControllerProvider.notifier).recarregar(),
          ),
          _ => RefreshIndicator(
            onRefresh: () =>
                ref.read(dashboardControllerProvider.notifier).recarregar(),
            child: _ConteudoDashboard(dados: dados),
          ),
        },
      ),
      bottomNavigationBar: switch (estado.valueOrNull?.tipo) {
        'cidadao' => const CitizenNavigation(selectedIndex: 0),
        'empresa' => const CompanyNavigation(selectedIndex: 0),
        'administrador' => const AdminNavigation(selectedIndex: 0),
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
                      'Visão geral da operação EcoTech.',
                      style: Theme.of(context).textTheme.bodyLarge,
                    ),
                    const SizedBox(height: 22),
                    _DashboardAdmin(dados),
                  ],
                ),
              ),
            ),
          ],
        );
      },
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
        Row(
          children: [
            Expanded(
              child: ElevatedButton.icon(
                onPressed: () => context.push('/empresa/operacoes'),
                icon: const Icon(Icons.inventory_2_outlined),
                label: const Text('Operações'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => context.push('/relatorios'),
                icon: const Icon(Icons.bar_chart_outlined),
                label: const Text('Relatórios'),
              ),
            ),
          ],
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
                      .map(
                        (solicitacao) => _SolicitacaoTile(
                          solicitacao,
                          onTap: () => context.push(
                            '/empresa/operacoes/${solicitacao.id}',
                          ),
                        ),
                      )
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

class _SolicitacaoTile extends StatelessWidget {
  const _SolicitacaoTile(this.solicitacao, {this.onTap});
  final SolicitacaoResumo solicitacao;
  final VoidCallback? onTap;
  @override
  Widget build(BuildContext context) => ListTile(
    contentPadding: EdgeInsets.zero,
    onTap: onTap,
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
