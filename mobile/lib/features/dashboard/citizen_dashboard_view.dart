import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../../data/dashboard/dashboard_data.dart';

const _background = Color(0xFFF7F9FA);
const _green = Color(0xFF2B7654);
const _darkGreen = Color(0xFF195638);
const _softGreen = Color(0xFFE2F2E8);
const _border = Color(0xFFDFE5E2);
const _muted = Color(0xFF5E6670);
const _gold = Color(0xFFFFD574);
const _goldSoft = Color(0xFFFFF5D6);
const _goldText = Color(0xFF6B4A00);

class CitizenDashboardView extends StatefulWidget {
  const CitizenDashboardView({
    required this.data,
    required this.onRefresh,
    super.key,
  });

  final DashboardData data;
  final Future<void> Function() onRefresh;

  @override
  State<CitizenDashboardView> createState() => _CitizenDashboardViewState();
}

class _CitizenDashboardViewState extends State<CitizenDashboardView> {
  bool _showAll = false;

  @override
  Widget build(BuildContext context) {
    final data = widget.data;
    final metrics = data.metricas;
    final firstName = data.usuario.nome.trim().split(RegExp(r'\s+')).first;
    final devices = (metrics['dispositivos'] as num?)?.toInt() ?? 0;
    final visibleDeliveries = data.entregas.take(_showAll ? 6 : 3).toList();
    return ColoredBox(
      color: _background,
      child: RefreshIndicator(
        onRefresh: widget.onRefresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: EdgeInsets.zero,
          children: [
            Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 560),
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 29, 16, 39),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 5),
                        child: Text(
                          'Bem-vindo de volta,',
                          style: TextStyle(
                            color: _muted,
                            fontSize: 14,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 5),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Expanded(
                              child: Text(
                                'Olá, $firstName!',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  fontSize: 31,
                                  height: 1.05,
                                  fontWeight: FontWeight.w700,
                                  color: Color(0xFF0D0F10),
                                ),
                              ),
                            ),
                            const SizedBox(width: 8),
                            _TierSummary(
                              tier: '${metrics['tier'] ?? '-'}',
                              devices: devices,
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 27),
                      _BalanceCard(metrics: metrics),
                      const SizedBox(height: 25),
                      _MissionCard(data: data),
                      const SizedBox(height: 38),
                      const _SectionHeader(
                        title: 'Ações rápidas',
                        trailing: 'O que deseja fazer?',
                      ),
                      const SizedBox(height: 20),
                      const Row(
                        children: [
                          Expanded(
                            child: _QuickAction(
                              icon: Icons.calendar_month_outlined,
                              title: 'Agendar coleta',
                              subtitle: 'Coleta em casa',
                              route: '/solicitacoes/nova',
                            ),
                          ),
                          SizedBox(width: 12),
                          Expanded(
                            child: _QuickAction(
                              icon: Icons.location_on_outlined,
                              title: 'Buscar ponto',
                              subtitle: 'Locais próximos',
                              route: '/pontos',
                            ),
                          ),
                          SizedBox(width: 12),
                          Expanded(
                            child: _QuickAction(
                              icon: Icons.monetization_on_outlined,
                              title: 'Sacar',
                              subtitle: 'Resgatar saldo',
                              route: '/carteira',
                              highlighted: true,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 42),
                      _DeliveriesHeader(
                        completed: data.totalEntregasConcluidas,
                      ),
                      const SizedBox(height: 20),
                      if (visibleDeliveries.isEmpty)
                        const _EmptyDeliveries()
                      else
                        ...visibleDeliveries.map(
                          (delivery) => Padding(
                            padding: const EdgeInsets.only(bottom: 14),
                            child: _DeliveryCard(delivery),
                          ),
                        ),
                      if (data.entregas.length > 3) ...[
                        const SizedBox(height: 2),
                        SizedBox(
                          width: double.infinity,
                          height: 55,
                          child: OutlinedButton.icon(
                            onPressed: () =>
                                setState(() => _showAll = !_showAll),
                            icon: Icon(
                              _showAll
                                  ? Icons.keyboard_arrow_up
                                  : Icons.keyboard_arrow_down,
                            ),
                            label: Text(
                              _showAll
                                  ? 'Mostrar menos'
                                  : 'Ver todas (${data.entregas.length})',
                            ),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: _darkGreen,
                              side: const BorderSide(color: Color(0xFFC9DDD2)),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(18),
                              ),
                              textStyle: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ),
                      ],
                      const SizedBox(height: 50),
                      const _CitizenFooter(),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TierSummary extends StatelessWidget {
  const _TierSummary({required this.tier, required this.devices});

  final String tier;
  final int devices;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.end,
    children: [
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: const Color(0xFFE9ECEF),
          borderRadius: BorderRadius.circular(15),
          boxShadow: const [BoxShadow(color: Color(0x1A000000), blurRadius: 5)],
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.military_tech_outlined, size: 16),
            const SizedBox(width: 4),
            Text(
              tier.toUpperCase(),
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
            ),
          ],
        ),
      ),
      const SizedBox(height: 6),
      Text(
        '$devices aparelhos reciclados',
        style: const TextStyle(
          color: _green,
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    ],
  );
}

class _BalanceCard extends StatelessWidget {
  const _BalanceCard({required this.metrics});

  final Map<String, dynamic> metrics;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.fromLTRB(25, 25, 25, 26),
    decoration: BoxDecoration(
      gradient: const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [Color(0xFF479268), Color(0xFF2D7652), Color(0xFF195437)],
      ),
      borderRadius: BorderRadius.circular(29),
      boxShadow: const [
        BoxShadow(
          color: Color(0x33256B49),
          blurRadius: 20,
          offset: Offset(0, 12),
        ),
      ],
    ),
    child: Column(
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: _BalanceValue(
                icon: Icons.account_balance_wallet_outlined,
                label: 'Saldo disponível',
                value: AppFormatters.moeda(metrics['saldo']),
                large: true,
              ),
            ),
            _BalanceValue(
              icon: Icons.auto_awesome_outlined,
              label: 'EcoPoints',
              value: _points(metrics['pontos']),
            ),
          ],
        ),
        const SizedBox(height: 35),
        SizedBox(
          width: double.infinity,
          height: 58,
          child: OutlinedButton(
            onPressed: () => context.push('/solicitacoes/nova'),
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.white,
              backgroundColor: Colors.white.withValues(alpha: .14),
              side: BorderSide(color: Colors.white.withValues(alpha: .25)),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(18),
              ),
            ),
            child: const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Flexible(
                  child: Text(
                    'Iniciar novo descarte',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                  ),
                ),
                SizedBox(width: 14),
                Icon(Icons.arrow_forward, size: 20),
              ],
            ),
          ),
        ),
      ],
    ),
  );

  static String _points(dynamic value) {
    final number = (value as num?)?.toInt() ?? 0;
    final digits = number.toString();
    final groups = <String>[];
    for (var end = digits.length; end > 0; end -= 3) {
      groups.insert(0, digits.substring(math.max(0, end - 3), end));
    }
    return groups.join('.');
  }
}

class _BalanceValue extends StatelessWidget {
  const _BalanceValue({
    required this.icon,
    required this.label,
    required this.value,
    this.large = false,
  });

  final IconData icon;
  final String label;
  final String value;
  final bool large;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: large
        ? CrossAxisAlignment.start
        : CrossAxisAlignment.end,
    children: [
      Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: const Color(0xFFD1E8DC), size: 18),
          const SizedBox(width: 8),
          Flexible(
            child: Text(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                color: Color(0xFFD6E8DE),
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
      const SizedBox(height: 9),
      Text(
        value,
        style: TextStyle(
          color: Colors.white,
          fontSize: large ? 34 : 24,
          fontWeight: FontWeight.w700,
          height: 1,
        ),
      ),
    ],
  );
}

class _MissionCard extends StatelessWidget {
  const _MissionCard({required this.data});

  final DashboardData data;

  @override
  Widget build(BuildContext context) {
    final mission = data.missao ?? const {};
    final current = (mission['atual'] as num?)?.toInt() ?? 0;
    final goal = (mission['meta'] as num?)?.toInt() ?? 1;
    final remaining = math.max(0, goal - current);
    final progress = goal <= 0 ? 0.0 : (current / goal).clamp(0, 1).toDouble();
    return Container(
      padding: const EdgeInsets.fromLTRB(25, 25, 25, 25),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(29),
        border: Border.all(color: const Color(0xFFE1E8E4)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x120E3D28),
            blurRadius: 10,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'MISSÃO ATUAL',
                      style: TextStyle(
                        color: _green,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${mission['titulo'] ?? 'Recicle seus aparelhos'}',
                      style: const TextStyle(
                        fontSize: 21,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: _softGreen,
                  borderRadius: BorderRadius.circular(18),
                ),
                child: Text(
                  '$current / $goal',
                  style: const TextStyle(
                    color: _darkGreen,
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 29),
          ClipRRect(
            borderRadius: BorderRadius.circular(8),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 14,
              backgroundColor: const Color(0xFFE7F0EB),
              valueColor: const AlwaysStoppedAnimation(Color(0xFF398961)),
            ),
          ),
          const SizedBox(height: 10),
          Text(
            remaining == 0
                ? 'Missão concluída'
                : 'Faltam só $remaining aparelhos para completar',
            style: const TextStyle(
              color: _muted,
              fontSize: 13,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 22),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: _goldSoft,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: const Color(0xFFFFDF8A)),
            ),
            child: Row(
              children: [
                Container(
                  width: 55,
                  height: 55,
                  decoration: const BoxDecoration(
                    color: _gold,
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.card_giftcard_outlined,
                    color: _goldText,
                    size: 25,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'PRÓXIMA RECOMPENSA',
                        style: TextStyle(
                          color: _goldText,
                          fontSize: 10,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '+${mission['recompensa_pontos'] ?? 0} pontos e 4 estrelas',
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
                const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.star, size: 14, color: _goldText),
                    Icon(Icons.star, size: 14, color: _goldText),
                    Icon(Icons.star, size: 14, color: _goldText),
                    Icon(Icons.star, size: 14, color: _goldText),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.trailing});

  final String title;
  final String trailing;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Expanded(
        child: Text(
          title,
          style: const TextStyle(fontSize: 23, fontWeight: FontWeight.w700),
        ),
      ),
      Text(
        trailing,
        style: const TextStyle(
          color: _muted,
          fontSize: 12,
          fontWeight: FontWeight.w600,
        ),
      ),
    ],
  );
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.route,
    this.highlighted = false,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final String route;
  final bool highlighted;

  @override
  Widget build(BuildContext context) => InkWell(
    borderRadius: BorderRadius.circular(23),
    onTap: () => context.push(route),
    child: Container(
      height: 162,
      padding: const EdgeInsets.fromLTRB(7, 20, 7, 18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(23),
        border: Border.all(color: _border),
        boxShadow: const [
          BoxShadow(
            color: Color(0x10000000),
            blurRadius: 7,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Container(
            width: 61,
            height: 61,
            decoration: BoxDecoration(
              color: highlighted ? _gold : _softGreen,
              borderRadius: BorderRadius.circular(22),
            ),
            child: Icon(
              icon,
              color: highlighted ? _goldText : _darkGreen,
              size: 23,
            ),
          ),
          const Spacer(),
          Text(
            title,
            maxLines: 1,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 9),
          Text(
            subtitle,
            maxLines: 1,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 10.5, color: Color(0xFF33383D)),
          ),
        ],
      ),
    ),
  );
}

class _DeliveriesHeader extends StatelessWidget {
  const _DeliveriesHeader({required this.completed});

  final int completed;

  @override
  Widget build(BuildContext context) => Row(
    crossAxisAlignment: CrossAxisAlignment.end,
    children: [
      const Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'SEU IMPACTO',
              style: TextStyle(
                color: _green,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'Últimas entregas',
              style: TextStyle(fontSize: 23, fontWeight: FontWeight.w700),
            ),
          ],
        ),
      ),
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 8),
        decoration: BoxDecoration(
          color: _softGreen,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.check, size: 17, color: _darkGreen),
            const SizedBox(width: 7),
            Text(
              '$completed concluídas',
              style: const TextStyle(
                color: _darkGreen,
                fontSize: 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    ],
  );
}

class _DeliveryCard extends StatelessWidget {
  const _DeliveryCard(this.delivery);

  final EntregaResumo delivery;

  @override
  Widget build(BuildContext context) {
    final finished = delivery.status.toLowerCase() == 'finalizado';
    return Container(
      padding: const EdgeInsets.fromLTRB(18, 17, 18, 17),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(25),
        border: Border.all(color: _border),
        boxShadow: const [
          BoxShadow(
            color: Color(0x10000000),
            blurRadius: 6,
            offset: Offset(0, 3),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 55,
            height: 55,
            decoration: BoxDecoration(
              color: _softGreen,
              borderRadius: BorderRadius.circular(19),
            ),
            child: Icon(
              finished
                  ? Icons.inventory_2_outlined
                  : Icons.devices_other_outlined,
              color: _darkGreen,
              size: 26,
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Incentivo por coleta',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 3),
                Text(
                  delivery.empresa,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: _muted,
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  AppFormatters.dataTexto(delivery.data),
                  style: const TextStyle(color: _muted, fontSize: 11),
                ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                AppFormatters.moeda(delivery.valor),
                style: const TextStyle(
                  color: _green,
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 7),
              Text(
                delivery.status.toUpperCase(),
                style: TextStyle(
                  color: finished ? _green : const Color(0xFFC33D3D),
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _EmptyDeliveries extends StatelessWidget {
  const _EmptyDeliveries();

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(24),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(25),
      border: Border.all(color: _border),
    ),
    child: const Text(
      'Você ainda não tem entregas no histórico.',
      textAlign: TextAlign.center,
      style: TextStyle(color: _muted),
    ),
  );
}

class _CitizenFooter extends StatelessWidget {
  const _CitizenFooter();

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.fromLTRB(25, 34, 25, 32),
    decoration: BoxDecoration(
      color: const Color(0xFF111416),
      borderRadius: BorderRadius.circular(30),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'ECOTECH',
          style: TextStyle(
            color: Color(0xFF39A16D),
            fontSize: 20,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 18),
        const Text(
          'Seu descarte transforma tecnologia antiga em impacto positivo.',
          style: TextStyle(
            color: Color(0xFFCED2D4),
            fontSize: 13,
            height: 1.75,
          ),
        ),
        const SizedBox(height: 17),
        TextButton.icon(
          onPressed: () => context.push('/entregas'),
          style: TextButton.styleFrom(
            foregroundColor: const Color(0xFF37A36B),
            padding: EdgeInsets.zero,
          ),
          label: const Text(
            'Ver meu histórico',
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
          ),
          iconAlignment: IconAlignment.end,
          icon: const Icon(Icons.arrow_forward, size: 17),
        ),
      ],
    ),
  );
}
