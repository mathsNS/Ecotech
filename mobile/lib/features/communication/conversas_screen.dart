import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/communication/communication_data.dart';
import '../../shared/widgets/app_back_button.dart';
import '../auth/auth_controller.dart';
import '../company/widgets/company_navigation.dart';
import '../company/widgets/company_states.dart';
import 'communication_controller.dart';
import 'widgets/communication_actions.dart';

class ConversasScreen extends ConsumerStatefulWidget {
  const ConversasScreen({super.key});

  @override
  ConsumerState<ConversasScreen> createState() => _ConversasScreenState();
}

class _ConversasScreenState extends ConsumerState<ConversasScreen> {
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(
      const Duration(seconds: 20),
      (_) => ref.invalidate(conversasProvider),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(conversasProvider);
    final userType = ref.watch(authControllerProvider).valueOrNull?.tipo;
    return Scaffold(
      appBar: AppBar(
        leading: const AppBackButton(),
        title: const Text('Conversas'),
        actions: const [CommunicationActions()],
      ),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(conversasProvider),
        ),
        data: (conversas) => RefreshIndicator(
          onRefresh: () => ref.refresh(conversasProvider.future),
          child: conversas.isEmpty
              ? ListView(
                  children: const [
                    SizedBox(height: 120),
                    CompanyEmpty(
                      message: 'Nenhuma conversa disponível. O chat aparece quando uma coleta recebe uma empresa.',
                    ),
                  ],
                )
              : ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  itemCount: conversas.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) =>
                      _ConversaTile(conversas[index]),
                ),
        ),
      ),
      bottomNavigationBar: userType == 'empresa'
          ? const CompanyNavigation(selectedIndex: 3)
          : null,
    );
  }
}

class _ConversaTile extends StatelessWidget {
  const _ConversaTile(this.conversa);
  final ConversaData conversa;

  @override
  Widget build(BuildContext context) => ListTile(
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
    onTap: () => context.push('/conversas/${conversa.solicitacaoId}'),
    leading: CircleAvatar(
      backgroundColor: conversa.naoLidas > 0
          ? AppColors.primary
          : AppColors.secondary,
      foregroundColor: conversa.naoLidas > 0 ? Colors.white : AppColors.primary,
      child: Icon(
        conversa.contatoTipo == 'empresa'
            ? Icons.business_outlined
            : Icons.person_outline,
      ),
    ),
    title: Row(
      children: [
        Expanded(
          child: Text(
            conversa.contatoNome,
            style: TextStyle(
              fontWeight: conversa.naoLidas > 0
                  ? FontWeight.w800
                  : FontWeight.w600,
            ),
          ),
        ),
        Text(
          AppFormatters.dataHoraTexto(conversa.ultimaMensagemEm),
          style: const TextStyle(fontSize: 11, color: AppColors.textLight),
        ),
      ],
    ),
    subtitle: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 4),
        Text(
          conversa.ultimaMensagem,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        const SizedBox(height: 4),
        Text(
          '#${conversa.solicitacaoId.substring(0, 8)} · ${conversa.estado}',
          style: const TextStyle(fontSize: 11, color: AppColors.textLight),
        ),
      ],
    ),
    trailing: conversa.naoLidas == 0
        ? const Icon(Icons.chevron_right)
        : Badge.count(count: conversa.naoLidas),
  );
}
