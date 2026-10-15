import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/finance/finance_data.dart';
import '../../shared/widgets/app_back_button.dart';
import '../citizen/widgets/citizen_navigation.dart';
import '../communication/widgets/communication_actions.dart';
import '../company/widgets/company_states.dart';
import 'finance_controller.dart';
import 'saque_screen.dart';
import 'widgets/wallet_balance_card.dart';
import 'widgets/withdrawal_receipt.dart';

class CarteiraScreen extends ConsumerWidget {
  const CarteiraScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(carteiraProvider);
    final horizontal = ((MediaQuery.sizeOf(context).width - 576) / 2).clamp(
      16.0,
      double.infinity,
    );
    return Scaffold(
      appBar: AppBar(
        leading: const AppBackButton(),
        title: const Text('Carteira'),
        backgroundColor: AppColors.surfaceSubtle,
        actions: const [CommunicationActions()],
      ),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(carteiraProvider),
        ),
        data: (carteira) => RefreshIndicator(
          onRefresh: () => ref.refresh(carteiraProvider.future),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: EdgeInsets.fromLTRB(horizontal, 16, horizontal, 32),
            children: [
              WalletBalanceCard(carteira),
              const SizedBox(height: 16),
              const Text(
                'Modo demonstrativo: os pedidos são registrados, sem transferência real de dinheiro.',
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: carteira.saldo <= 0 || carteira.metodos.isEmpty
                      ? null
                      : () => Navigator.of(context).push(
                          MaterialPageRoute<void>(
                            builder: (_) => SaqueScreen(wallet: carteira),
                          ),
                        ),
                  icon: const Icon(Icons.account_balance_wallet_outlined),
                  label: const Text('Solicitar saque'),
                ),
              ),
              const SizedBox(height: 22),
              Text(
                'Histórico de saques',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 8),
              if (carteira.saques.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(18),
                    child: Text('Nenhum saque solicitado até o momento.'),
                  ),
                )
              else
                ...carteira.saques.map(_SaqueTile.new),
            ],
          ),
        ),
      ),
      bottomNavigationBar: const CitizenNavigation(selectedIndex: 2),
    );
  }
}

class _SaqueTile extends StatelessWidget {
  const _SaqueTile(this.saque);

  final SaqueData saque;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 12),
    child: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Wrap(
            spacing: 16,
            runSpacing: 8,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              Text(
                AppFormatters.moeda(saque.valor),
                style: Theme.of(context).textTheme.titleMedium,
              ),
              _StatusSaque(saque.status),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            saque.metodo == 'Transferencia' ? 'Transferência' : saque.metodo,
          ),
          Text(AppFormatters.dataHoraTexto(saque.dataHora)),
          const SizedBox(height: 8),
          TextButton.icon(
            icon: const Icon(Icons.receipt_long_outlined),
            label: const Text('Ver registro'),
            onPressed: () => showDialog<void>(
              context: context,
              builder: (dialogContext) => Dialog(
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      WithdrawalReceipt(saque),
                      TextButton(
                        onPressed: () => Navigator.pop(dialogContext),
                        child: const Text('Fechar'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    ),
  );
}

class _StatusSaque extends StatelessWidget {
  const _StatusSaque(this.status);

  final String status;

  @override
  Widget build(BuildContext context) {
    final cancelado = status.toLowerCase() == 'cancelado';
    final finalizado = status.toLowerCase() == 'finalizado';
    final cor = cancelado
        ? AppColors.error
        : finalizado
        ? AppColors.success
        : AppColors.warning;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: cor.withValues(alpha: .12),
        borderRadius: BorderRadius.circular(15),
      ),
      child: Text(
        status.isEmpty ? 'Pendente' : status,
        style: TextStyle(color: cor, fontSize: 11, fontWeight: FontWeight.w700),
      ),
    );
  }
}
