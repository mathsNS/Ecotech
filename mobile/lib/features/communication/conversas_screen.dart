import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/communication/communication_data.dart';
import '../auth/auth_controller.dart';
import '../citizen/widgets/citizen_navigation.dart';
import '../company/widgets/company_navigation.dart';
import '../company/widgets/company_states.dart';
import 'communication_controller.dart';
import '../dashboard/dashboard_header.dart';
import '../operations/operations_widgets.dart';

class ConversasScreen extends ConsumerStatefulWidget {
  const ConversasScreen({super.key});

  @override
  ConsumerState<ConversasScreen> createState() => _ConversasScreenState();
}

class _ConversasScreenState extends ConsumerState<ConversasScreen> {
  Timer? _timer;
  String _busca = '';

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
    final usuario = ref.watch(authControllerProvider).valueOrNull;
    final userType = usuario?.tipo;
    return Scaffold(
      backgroundColor: operationsBackground,
      appBar: EcoTechDashboardHeader(name: usuario?.nome ?? 'EcoTech'),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(conversasProvider),
        ),
        data: (conversas) {
          final filtradas = conversas
              .where(
                (item) =>
                    item.contatoNome.toLowerCase().contains(_busca) ||
                    item.solicitacaoId.toLowerCase().contains(_busca),
              )
              .toList();
          final naoLidas = conversas.fold<int>(
            0,
            (total, item) => total + item.naoLidas,
          );
          return RefreshIndicator(
            onRefresh: () => ref.refresh(conversasProvider.future),
            child: CustomScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              slivers: [
                SliverPadding(
                  padding: const EdgeInsets.fromLTRB(20, 26, 20, 24),
                  sliver: SliverToBoxAdapter(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Central de conversas',
                          style: TextStyle(
                            fontSize: 28,
                            fontWeight: FontWeight.w800,
                            letterSpacing: -.8,
                            color: operationsDark,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          userType == 'empresa'
                              ? 'Selecione um cliente ou uma coleta para continuar o atendimento.'
                              : 'Selecione uma conversa para acompanhar sua coleta.',
                          style: const TextStyle(
                            fontSize: 15,
                            height: 1.5,
                            color: operationsMuted,
                          ),
                        ),
                        const SizedBox(height: 20),
                        TextField(
                          onChanged: (value) => setState(
                            () => _busca = value.trim().toLowerCase(),
                          ),
                          decoration: InputDecoration(
                            hintText: userType == 'empresa'
                                ? 'Buscar por cliente ou coleta'
                                : 'Buscar por contato ou coleta',
                            hintStyle: const TextStyle(
                              fontSize: 14,
                              color: operationsMuted,
                            ),
                            prefixIcon: const Icon(
                              Icons.search,
                              color: operationsMuted,
                            ),
                            fillColor: Colors.white,
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: const BorderSide(
                                color: operationsBorder,
                              ),
                            ),
                            enabledBorder: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(30),
                              borderSide: const BorderSide(
                                color: operationsBorder,
                              ),
                            ),
                            contentPadding: const EdgeInsets.symmetric(
                              horizontal: 18,
                              vertical: 16,
                            ),
                          ),
                        ),
                        const SizedBox(height: 14),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 14,
                          ),
                          decoration: BoxDecoration(
                            color: operationsSoftGreen,
                            borderRadius: BorderRadius.circular(28),
                          ),
                          child: Row(
                            children: [
                              const Icon(
                                Icons.verified_user_outlined,
                                color: operationsDeepGreen,
                                size: 20,
                              ),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  'Canal privado por coleta. ${naoLidas == 0 ? 'Nenhuma mensagem não lida.' : '$naoLidas ${naoLidas == 1 ? 'mensagem não lida' : 'mensagens não lidas'}.'}',
                                  style: const TextStyle(
                                    fontSize: 13,
                                    color: operationsDeepGreen,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                if (filtradas.isEmpty)
                  SliverToBoxAdapter(
                    child: CompanyEmpty(
                      message: conversas.isEmpty
                          ? 'Nenhuma conversa disponível. O chat aparece quando uma coleta recebe uma empresa.'
                          : 'Nenhuma conversa encontrada para esta busca.',
                    ),
                  )
                else
                  SliverPadding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    sliver: SliverList.builder(
                      itemCount: filtradas.length,
                      itemBuilder: (context, index) => Padding(
                        padding: const EdgeInsets.only(bottom: 14),
                        child: _ConversaTile(filtradas[index]),
                      ),
                    ),
                  ),
                const SliverToBoxAdapter(child: SizedBox(height: 44)),
                SliverFillRemaining(
                  hasScrollBody: false,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      Container(
                        width: double.infinity,
                        color: const Color(0xFF101315),
                        padding: const EdgeInsets.symmetric(
                          horizontal: 20,
                          vertical: 36,
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'ECOTECH',
                              style: TextStyle(
                                fontSize: 22,
                                fontWeight: FontWeight.w800,
                                color: AppColors.primary,
                              ),
                            ),
                            const SizedBox(height: 18),
                            Text(
                              userType == 'empresa'
                                  ? 'Fale direto com quem solicitou a coleta, sem sair do fluxo da operação.'
                                  : 'Converse com a empresa responsável e acompanhe sua coleta.',
                              style: const TextStyle(
                                color: Color(0xFFCCD0CE),
                                fontSize: 15,
                                height: 1.6,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
      bottomNavigationBar: switch (userType) {
        'empresa' => const CompanyNavigation(selectedIndex: 3),
        'cidadao' => const CitizenNavigation(selectedIndex: 4),
        _ => null,
      },
    );
  }
}

class _ConversaTile extends StatelessWidget {
  const _ConversaTile(this.conversa);
  final ConversaData conversa;

  @override
  Widget build(BuildContext context) => Material(
    color: Colors.white,
    elevation: 1,
    shadowColor: const Color(0x22000000),
    borderRadius: BorderRadius.circular(26),
    clipBehavior: Clip.antiAlias,
    child: ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      onTap: () => context.push('/conversas/${conversa.solicitacaoId}'),
      minVerticalPadding: 20,
      leading: Badge.count(
        count: conversa.naoLidas,
        isLabelVisible: conversa.naoLidas > 0,
        backgroundColor: const Color(0xFFE30620),
        child: CircleAvatar(
          radius: 27,
          backgroundColor: operationsSoftGreen,
          foregroundColor: operationsDeepGreen,
          child: Text(
            conversa.contatoNome.trim().isEmpty
                ? 'E'
                : conversa.contatoNome.trim().substring(0, 1).toUpperCase(),
            style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w700),
          ),
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
            _hora(conversa.ultimaMensagemEm),
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
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFFEAF1ED),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              'Coleta #${conversa.solicitacaoId.length > 8 ? conversa.solicitacaoId.substring(0, 8) : conversa.solicitacaoId}',
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: operationsDeepGreen,
              ),
            ),
          ),
          if (conversa.encerrada)
            const Text(
              'Conversa encerrada',
              style: TextStyle(fontSize: 11, color: operationsMuted),
            ),
        ],
      ),
      trailing: const Icon(Icons.chevron_right, color: operationsMuted),
    ),
  );

  String _hora(String value) {
    final date = DateTime.tryParse(value);
    if (date == null) return AppFormatters.dataHoraTexto(value);
    final hoje = DateTime.now();
    if (date.year != hoje.year ||
        date.month != hoje.month ||
        date.day != hoje.day) {
      return AppFormatters.data(date, curta: true);
    }
    return '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
  }
}
