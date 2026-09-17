import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/dashboard/dashboard_data.dart';
import '../communication/communication_controller.dart';

const _pageBackground = Color(0xFFF6F7F8);
const _cardBorder = Color(0xFFE9EBED);
const _deepGreen = Color(0xFF1E5D3B);
const _softGreen = Color(0xFFEAF3EE);

class CompanyDashboardHeader extends ConsumerStatefulWidget
    implements PreferredSizeWidget {
  const CompanyDashboardHeader({required this.name, super.key});

  final String name;

  @override
  Size get preferredSize => const Size.fromHeight(60);

  @override
  ConsumerState<CompanyDashboardHeader> createState() =>
      _CompanyDashboardHeaderState();
}

class _CompanyDashboardHeaderState
    extends ConsumerState<CompanyDashboardHeader> {
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => ref.invalidate(badgesProvider),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final notifications =
        ref.watch(badgesProvider).valueOrNull?.notificacoes ?? 0;
    final initial = widget.name.trim().isEmpty
        ? 'E'
        : widget.name.trim().substring(0, 1).toUpperCase();
    return AppBar(
      toolbarHeight: 60,
      backgroundColor: const Color(0xFFF2F6F3),
      shape: const Border(bottom: BorderSide(color: Color(0xFFDDE4E0))),
      titleSpacing: 16,
      title: Image.asset(
        'assets/images/ecotech navbar.png',
        width: 104,
        fit: BoxFit.contain,
      ),
      actions: [
        IconButton(
          tooltip: 'Notificações',
          onPressed: () => context.push('/notificacoes'),
          icon: Badge.count(
            count: notifications,
            isLabelVisible: notifications > 0,
            backgroundColor: const Color(0xFFE31D2D),
            child: const Icon(Icons.notifications_none_rounded, size: 25),
          ),
        ),
        const SizedBox(width: 4),
        Semantics(
          button: true,
          label: 'Abrir perfil',
          child: InkWell(
            customBorder: const CircleBorder(),
            onTap: () => context.go('/perfil'),
            child: CircleAvatar(
              radius: 19,
              backgroundColor: const Color(0xFFDFF0E6),
              child: Text(
                initial,
                style: const TextStyle(
                  color: _deepGreen,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
        ),
        const SizedBox(width: 16),
      ],
    );
  }
}

class CompanyDashboardNavigation extends StatelessWidget {
  const CompanyDashboardNavigation({super.key});

  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: const BoxDecoration(
      color: Colors.white,
      border: Border(top: BorderSide(color: Color(0xFFDDE1E4))),
    ),
    child: SafeArea(
      top: false,
      child: SizedBox(
        height: 72,
        child: Row(
          children: [
            _NavItem(
              icon: Icons.grid_view_rounded,
              label: 'Dashboard',
              selected: true,
              onTap: () {},
            ),
            _NavItem(
              icon: Icons.inventory_2_outlined,
              label: 'Operações',
              onTap: () => context.go('/empresa/operacoes'),
            ),
            _NavItem(
              icon: Icons.insert_chart_outlined_rounded,
              label: 'Relatórios',
              onTap: () => context.go('/relatorios'),
            ),
            _NavItem(
              icon: Icons.chat_bubble_outline_rounded,
              label: 'Conversas',
              onTap: () => context.go('/conversas'),
            ),
            _NavItem(
              icon: Icons.menu_rounded,
              label: 'Mais',
              onTap: () => _showMore(context),
            ),
          ],
        ),
      ),
    ),
  );

  static Future<void> _showMore(BuildContext context) => showModalBottomSheet(
    context: context,
    showDragHandle: true,
    builder: (sheetContext) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 18),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _MoreItem(
              icon: Icons.campaign_outlined,
              label: 'Oportunidades',
              route: '/empresa/oportunidades',
            ),
            _MoreItem(
              icon: Icons.location_on_outlined,
              label: 'Pontos de coleta',
              route: '/empresa/pontos',
            ),
            _MoreItem(
              icon: Icons.warehouse_outlined,
              label: 'Bases operacionais',
              route: '/empresa/bases',
            ),
            _MoreItem(
              icon: Icons.workspace_premium_outlined,
              label: 'Planos',
              route: '/planos',
            ),
            _MoreItem(
              icon: Icons.person_outline,
              label: 'Perfil',
              route: '/perfil',
            ),
          ],
        ),
      ),
    ),
  );
}

class _NavItem extends StatelessWidget {
  const _NavItem({
    required this.icon,
    required this.label,
    required this.onTap,
    this.selected = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool selected;

  @override
  Widget build(BuildContext context) => Expanded(
    child: InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 7),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 34,
              height: 30,
              decoration: BoxDecoration(
                color: selected ? _softGreen : Colors.transparent,
                borderRadius: BorderRadius.circular(18),
              ),
              child: Icon(
                icon,
                size: 22,
                color: selected ? AppColors.primary : const Color(0xFF56606A),
              ),
            ),
            const SizedBox(height: 2),
            Text(
              label,
              maxLines: 1,
              style: TextStyle(
                fontSize: 10.5,
                color: selected ? AppColors.primary : const Color(0xFF56606A),
                fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    ),
  );
}

class _MoreItem extends StatelessWidget {
  const _MoreItem({
    required this.icon,
    required this.label,
    required this.route,
  });

  final IconData icon;
  final String label;
  final String route;

  @override
  Widget build(BuildContext context) => ListTile(
    leading: Icon(icon, color: AppColors.primary),
    title: Text(label),
    trailing: const Icon(Icons.chevron_right),
    onTap: () {
      final router = GoRouter.of(context);
      Navigator.pop(context);
      router.go(route);
    },
  );
}

class CompanyDashboardView extends StatelessWidget {
  const CompanyDashboardView({
    required this.data,
    required this.onRefresh,
    super.key,
  });

  final DashboardData data;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final firstName = data.usuario.nome.trim().split(RegExp(r'\s+')).first;
    final weight =
        (data.metricas['peso_processado_kg'] as num?)?.toDouble() ?? 0;
    return ColoredBox(
      color: _pageBackground,
      child: RefreshIndicator(
        onRefresh: onRefresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: EdgeInsets.zero,
          children: [
            Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 560),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 26, 16, 38),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Olá, $firstName!',
                        style: const TextStyle(
                          fontSize: 30,
                          height: 1.08,
                          fontWeight: FontWeight.w800,
                          letterSpacing: -1.1,
                          color: Color(0xFF111315),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Sua empresa já processou ${_weight(weight)}kg de lixo eletrônico',
                        style: const TextStyle(
                          fontSize: 13.5,
                          color: Color(0xFF5D6268),
                        ),
                      ),
                      const SizedBox(height: 21),
                      _MonthlySummary(data),
                      const SizedBox(height: 33),
                      const Text(
                        'Desempenho e impacto',
                        style: _SectionStyles.title,
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        'Visão dos últimos seis meses e distribuição dos materiais processados.',
                        style: _SectionStyles.subtitle,
                      ),
                      const SizedBox(height: 17),
                      _PerformanceCard(data),
                      const SizedBox(height: 32),
                      _ProcessingSection(data),
                      const SizedBox(height: 33),
                      const Text('Ações rápidas', style: _SectionStyles.title),
                      const SizedBox(height: 16),
                      const Row(
                        children: [
                          Expanded(
                            child: _QuickAction(
                              icon: Icons.location_on_outlined,
                              title: 'Pontos de Coleta',
                              subtitle: 'Gerencie entregas',
                              button: 'Gerenciar',
                              route: '/empresa/pontos',
                            ),
                          ),
                          SizedBox(width: 10),
                          Expanded(
                            child: _QuickAction(
                              icon: Icons.nature_people_outlined,
                              title: 'Seu plano',
                              subtitle: 'Veja e atualize',
                              button: 'Ver planos',
                              route: '/planos',
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const _CompanyFooter(),
          ],
        ),
      ),
    );
  }

  static String _weight(double value) => value.toStringAsFixed(1);
}

abstract final class _SectionStyles {
  static const title = TextStyle(
    fontSize: 21,
    height: 1.2,
    fontWeight: FontWeight.w800,
    letterSpacing: -0.55,
    color: Color(0xFF151719),
  );
  static const subtitle = TextStyle(
    fontSize: 13.5,
    height: 1.55,
    color: Color(0xFF5D6268),
  );
}

class _MonthlySummary extends StatelessWidget {
  const _MonthlySummary(this.data);

  final DashboardData data;

  @override
  Widget build(BuildContext context) {
    final metrics = data.metricas;
    final weight = (metrics['peso_processado_kg'] as num?)?.toDouble() ?? 0;
    final finished = (metrics['finalizadas'] as num?)?.toInt() ?? 0;
    final active = (metrics['ativas'] as num?)?.toInt() ?? 0;
    final activeMonth = data.meses.reversed
        .where((month) => month.pesoKg > 0)
        .map((month) => _monthName(month.mes))
        .firstOrNull;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(20, 19, 20, 22),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF2A6C4D), Color(0xFF174E31)],
        ),
        borderRadius: BorderRadius.circular(19),
        boxShadow: const [
          BoxShadow(
            color: Color(0x240F3322),
            blurRadius: 12,
            offset: Offset(0, 7),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Resumo do mês',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      activeMonth == null
                          ? 'Aguardando a primeira movimentação'
                          : '$activeMonth está movimentado',
                      style: const TextStyle(
                        color: Color(0xFFD2E3DA),
                        fontSize: 11.5,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                width: 38,
                height: 38,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: .14),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.eco_outlined,
                  color: Colors.white,
                  size: 23,
                ),
              ),
            ],
          ),
          const SizedBox(height: 25),
          Row(
            children: [
              Expanded(
                child: _SummaryValue(
                  label: 'Peso processado',
                  value: '${weight.toStringAsFixed(1)}kg',
                  icon: Icons.devices_other_outlined,
                ),
              ),
              Expanded(
                child: _SummaryValue(
                  label: 'Receita recebida',
                  value: AppFormatters.moeda(metrics['saldo']),
                  icon: Icons.payments_outlined,
                  warm: true,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Wrap(
            spacing: 10,
            runSpacing: 8,
            children: [
              _SummaryPill(
                icon: Icons.emoji_events_outlined,
                text: '$finished Finalizadas',
              ),
              _SummaryPill(
                icon: Icons.nature_people_outlined,
                text: '$active Operações ativas',
                strong: true,
              ),
            ],
          ),
        ],
      ),
    );
  }

  static String _monthName(String value) {
    const names = [
      'Janeiro',
      'Fevereiro',
      'Março',
      'Abril',
      'Maio',
      'Junho',
      'Julho',
      'Agosto',
      'Setembro',
      'Outubro',
      'Novembro',
      'Dezembro',
    ];
    final month = int.tryParse(value.split('/').first);
    return month != null && month >= 1 && month <= 12
        ? names[month - 1]
        : value;
  }
}

class _SummaryValue extends StatelessWidget {
  const _SummaryValue({
    required this.label,
    required this.value,
    required this.icon,
    this.warm = false,
  });

  final String label;
  final String value;
  final IconData icon;
  final bool warm;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(
        label,
        style: const TextStyle(color: Color(0xFFC5D9CE), fontSize: 11.5),
      ),
      const SizedBox(height: 5),
      Text(
        value,
        maxLines: 1,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 24,
          fontWeight: FontWeight.w800,
          letterSpacing: -.4,
        ),
      ),
      const SizedBox(height: 11),
      Container(
        width: 33,
        height: 33,
        decoration: BoxDecoration(
          color: warm
              ? const Color(0xFF94751E).withValues(alpha: .55)
              : const Color(0xFF29805A).withValues(alpha: .62),
          shape: BoxShape.circle,
        ),
        child: Icon(
          icon,
          size: 17,
          color: warm ? const Color(0xFFD8A737) : const Color(0xFF43A57C),
        ),
      ),
    ],
  );
}

class _SummaryPill extends StatelessWidget {
  const _SummaryPill({
    required this.icon,
    required this.text,
    this.strong = false,
  });

  final IconData icon;
  final String text;
  final bool strong;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
    decoration: BoxDecoration(
      color: Colors.white.withValues(alpha: strong ? .055 : .025),
      borderRadius: BorderRadius.circular(14),
    ),
    child: Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(
          icon,
          size: 14,
          color: Colors.white.withValues(alpha: strong ? .35 : .10),
        ),
        const SizedBox(width: 6),
        Text(
          text,
          style: TextStyle(
            color: Colors.white.withValues(alpha: strong ? .34 : .10),
            fontSize: 11.5,
          ),
        ),
      ],
    ),
  );
}

class _PerformanceCard extends StatelessWidget {
  const _PerformanceCard(this.data);

  final DashboardData data;

  @override
  Widget build(BuildContext context) {
    final categoryMax = data.categorias.fold<double>(
      0,
      (value, category) => math.max(value, category.pesoKg),
    );
    return Container(
      padding: const EdgeInsets.fromLTRB(15, 18, 15, 15),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(19),
        border: Border.all(color: _cardBorder),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0D000000),
            blurRadius: 3,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  'Peso processado por mês',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: _softGreen,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  '6 meses',
                  style: TextStyle(
                    color: AppColors.primary,
                    fontSize: 9.5,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 5),
          Text(
            data.comparativoMensal == null
                ? 'Comparativo disponível após dois meses com movimentação'
                : '${data.comparativoMensal! >= 0 ? '+' : ''}${AppFormatters.numero(data.comparativoMensal)}% comparado ao mês anterior',
            style: const TextStyle(fontSize: 11, color: Color(0xFF5D6268)),
          ),
          const SizedBox(height: 17),
          _MonthlyChart(data.meses),
          const SizedBox(height: 20),
          _ImpactMetrics(data.metricas),
          if (data.categorias.isNotEmpty) ...[
            const SizedBox(height: 19),
            ...data.categorias
                .take(3)
                .map((category) => _CategoryProgress(category, categoryMax)),
          ],
        ],
      ),
    );
  }
}

class _MonthlyChart extends StatelessWidget {
  const _MonthlyChart(this.months);

  final List<MesDashboard> months;

  @override
  Widget build(BuildContext context) {
    final maxWeight = months.fold<double>(
      0,
      (value, item) => math.max(value, item.pesoKg),
    );
    return SizedBox(
      height: 164,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: months.map((month) {
          final active = month.pesoKg > 0;
          final height = active && maxWeight > 0
              ? math.max(38.0, 120 * month.pesoKg / maxWeight)
              : 39.0;
          return Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Text(
                    active ? '${month.pesoKg.toStringAsFixed(0)} kg' : '-',
                    style: TextStyle(
                      fontSize: 10.5,
                      fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                    ),
                  ),
                  const SizedBox(height: 7),
                  Container(
                    height: height,
                    decoration: BoxDecoration(
                      color: active
                          ? const Color(0xFF398A62)
                          : const Color(0xFFF0F3F5),
                      borderRadius: const BorderRadius.vertical(
                        top: Radius.circular(11),
                      ),
                    ),
                  ),
                  const SizedBox(height: 7),
                  Text(
                    month.mes,
                    style: const TextStyle(
                      fontSize: 9.5,
                      color: Color(0xFF60666C),
                    ),
                  ),
                ],
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}

class _ImpactMetrics extends StatelessWidget {
  const _ImpactMetrics(this.metrics);

  final Map<String, dynamic> metrics;

  @override
  Widget build(BuildContext context) {
    final items = [
      (
        '${((metrics['co2_evitado_kg'] as num?)?.toDouble() ?? 0).toStringAsFixed(1)}kg',
        'CO₂ evitado',
      ),
      (
        '${((metrics['taxa_reciclagem_percentual'] as num?)?.toDouble() ?? 0).toStringAsFixed(1)}%',
        'taxa de\nreciclagem',
      ),
      (
        '${((metrics['peso_processado_kg'] as num?)?.toDouble() ?? 0).toStringAsFixed(1)}kg',
        'peso processado',
      ),
    ];
    return Row(
      children: [
        for (var index = 0; index < items.length; index++) ...[
          if (index > 0) const SizedBox(width: 8),
          Expanded(
            child: Container(
              height: 76,
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFFF2F6F4),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    items[index].$1,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    items[index].$2,
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                      fontSize: 9.5,
                      height: 1.25,
                      color: Color(0xFF5D6268),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _CategoryProgress extends StatelessWidget {
  const _CategoryProgress(this.category, this.maxWeight);

  final CategoriaDashboard category;
  final double maxWeight;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 13),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  category.nome,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              Text(
                '${category.pesoKg.toStringAsFixed(1)} kg',
                style: const TextStyle(
                  fontSize: 13,
                  color: Color(0xFF62686E),
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(5),
            child: LinearProgressIndicator(
              value: maxWeight <= 0
                  ? 0
                  : (category.pesoKg / maxWeight).clamp(0, 1).toDouble(),
              minHeight: 7,
              backgroundColor: const Color(0xFFE8EDEF),
              valueColor: const AlwaysStoppedAnimation(Color(0xFF34865E)),
            ),
          ),
        ],
      ),
    );
  }
}

class _ProcessingSection extends StatelessWidget {
  const _ProcessingSection(this.data);

  final DashboardData data;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const Expanded(
            child: Text(
              'Solicitações em\nprocessamento',
              style: _SectionStyles.title,
            ),
          ),
          TextButton(
            onPressed: () => context.go('/empresa/operacoes'),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Ver todas'),
                SizedBox(width: 5),
                Icon(Icons.arrow_outward_rounded, size: 16),
              ],
            ),
          ),
        ],
      ),
      const SizedBox(height: 15),
      if (data.emProcessamento.isEmpty)
        const _EmptyProcessing()
      else
        ...data.emProcessamento
            .take(2)
            .map(
              (request) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _ProcessingCard(request),
              ),
            ),
    ],
  );
}

class _ProcessingCard extends StatelessWidget {
  const _ProcessingCard(this.request);

  final SolicitacaoResumo request;

  @override
  Widget build(BuildContext context) {
    final shortId = request.id.substring(0, math.min(8, request.id.length));
    final location =
        request.baseOperacional ?? request.pontoColeta ?? request.cidadao;
    return InkWell(
      borderRadius: BorderRadius.circular(19),
      onTap: () => context.go('/empresa/operacoes/${request.id}'),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 13),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(19),
          border: Border.all(color: _cardBorder),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0D000000),
              blurRadius: 3,
              offset: Offset(0, 2),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: const BoxDecoration(
                color: _softGreen,
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.inventory_2_outlined,
                color: AppColors.primary,
                size: 22,
              ),
            ),
            const SizedBox(width: 11),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Solicitação #$shortId',
                    style: const TextStyle(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    '${request.pesoKg.toStringAsFixed(2)}kg - $location',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 11,
                      color: Color(0xFF62686E),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 9,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFE7A7),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Text(
                          'EM PROCESSAMENTO',
                          style: TextStyle(
                            color: Color(0xFF8B5A00),
                            fontSize: 9,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Text(
                        AppFormatters.data(request.dataCriacao, curta: true),
                        style: const TextStyle(
                          fontSize: 10.5,
                          color: Color(0xFF62686E),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyProcessing extends StatelessWidget {
  const _EmptyProcessing();

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(20),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(19),
      border: Border.all(color: _cardBorder),
    ),
    child: const Text(
      'Nenhuma solicitação em processamento.',
      textAlign: TextAlign.center,
      style: TextStyle(color: Color(0xFF62686E)),
    ),
  );
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.button,
    required this.route,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final String button;
  final String route;

  @override
  Widget build(BuildContext context) => Container(
    height: 174,
    padding: const EdgeInsets.all(15),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(19),
      border: Border.all(color: _cardBorder),
      boxShadow: const [
        BoxShadow(
          color: Color(0x0D000000),
          blurRadius: 3,
          offset: Offset(0, 2),
        ),
      ],
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: const BoxDecoration(
            color: Color(0xFFE1F4E8),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: _deepGreen, size: 22),
        ),
        const Spacer(),
        Text(
          title,
          maxLines: 1,
          style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 4),
        Text(
          subtitle,
          style: const TextStyle(fontSize: 11, color: Color(0xFF62686E)),
        ),
        const SizedBox(height: 11),
        SizedBox(
          width: double.infinity,
          height: 37,
          child: ElevatedButton(
            onPressed: () => context.go(route),
            style: ElevatedButton.styleFrom(
              padding: EdgeInsets.zero,
              backgroundColor: _deepGreen,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(11),
              ),
            ),
            child: Text(
              button,
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
            ),
          ),
        ),
      ],
    ),
  );
}

class _CompanyFooter extends StatelessWidget {
  const _CompanyFooter();

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    color: const Color(0xFF111416),
    padding: const EdgeInsets.fromLTRB(16, 34, 16, 34),
    child: Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 560),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'ECOTECH',
              style: TextStyle(
                color: Color(0xFF2D805B),
                fontSize: 18,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 18),
            const Text(
              '85% dos brasileiros guardam aparelhos sem uso. A EcoTech dá um destino correto, e você ainda é recompensado.',
              style: TextStyle(
                color: Color(0xFFD7D9DA),
                fontSize: 13.5,
                height: 1.65,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Links Rápidos',
              style: TextStyle(
                color: Colors.white,
                fontSize: 13.5,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 7),
            _FooterLink(label: 'Início', onTap: () => context.go('/home')),
            _FooterLink(
              label: 'Pontos de Coleta',
              onTap: () => context.go('/empresa/pontos'),
            ),
            _FooterLink(
              label: 'Criar Conta',
              onTap: () => context.go('/cadastro'),
            ),
            const SizedBox(height: 21),
            const Text(
              '© 2026 EcoTech. Todos os direitos reservados.',
              style: TextStyle(color: Color(0xFF9DA1A4), fontSize: 11.5),
            ),
          ],
        ),
      ),
    ),
  );
}

class _FooterLink extends StatelessWidget {
  const _FooterLink({required this.label, required this.onTap});

  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => InkWell(
    onTap: onTap,
    child: Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Text(
        label,
        style: const TextStyle(color: Color(0xFFD7D9DA), fontSize: 13.5),
      ),
    ),
  );
}
