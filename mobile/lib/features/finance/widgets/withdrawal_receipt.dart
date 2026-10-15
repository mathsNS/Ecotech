import 'package:flutter/material.dart';

import '../../../core/formatters/app_formatters.dart';
import '../../../core/theme/app_colors.dart';
import '../../../data/finance/finance_data.dart';

class WithdrawalReceipt extends StatelessWidget {
  const WithdrawalReceipt(this.withdrawal, {super.key});
  final SaqueData withdrawal;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Icon(
            Icons.receipt_long_outlined,
            size: 48,
            color: AppColors.primary,
          ),
          const SizedBox(height: 16),
          Text(
            'Registro do saque',
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 16),
          Text(
            AppFormatters.moeda(withdrawal.valor),
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 24),
          Text('Método: ${withdrawal.metodo}'),
          if (withdrawal.titular != null)
            Text('Titular: ${withdrawal.titular}'),
          Text(
            'Status: ${withdrawal.status.isEmpty ? 'Pendente' : withdrawal.status}',
          ),
          const SizedBox(height: 12),
          SelectableText('Protocolo: ${withdrawal.id}'),
          Text('Data: ${AppFormatters.dataHoraTexto(withdrawal.dataHora)}'),
          const Divider(height: 32),
          const Text(
            'Registro demonstrativo. Não comprova transferência de dinheiro.',
            textAlign: TextAlign.center,
          ),
        ],
      ),
    ),
  );
}
