import 'package:flutter/material.dart';

import '../../../core/formatters/app_formatters.dart';
import '../../../core/theme/app_colors.dart';
import '../../../data/finance/finance_data.dart';

class WalletBalanceCard extends StatelessWidget {
  const WalletBalanceCard(this.wallet, {super.key});
  final CarteiraData wallet;

  @override
  Widget build(BuildContext context) => Container(
    width: double.infinity,
    padding: const EdgeInsets.all(22),
    decoration: BoxDecoration(
      borderRadius: BorderRadius.circular(24),
      gradient: const LinearGradient(
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
        colors: [AppColors.primaryLight, AppColors.primaryDark],
      ),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Row(
          children: [
            Icon(
              Icons.account_balance_wallet_outlined,
              color: Colors.white,
              size: 20,
            ),
            SizedBox(width: 8),
            Expanded(
              child: Text(
                'Saldo disponível',
                style: TextStyle(color: Colors.white),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Text(
          AppFormatters.moeda(wallet.saldo),
          style: Theme.of(context).textTheme.headlineMedium
              ?.copyWith(color: Colors.white, fontWeight: FontWeight.w900),
        ),
        const SizedBox(height: 12),
        Text(
          '${wallet.pontos} EcoPontos acumulados',
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          '${wallet.pontosPorReal} pontos = R\$ 1,00',
          style: const TextStyle(color: Colors.white),
        ),
      ],
    ),
  );
}
