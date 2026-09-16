import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/communication/communication_data.dart';
import '../company/widgets/company_states.dart';
import 'communication_controller.dart';

class NotificacoesScreen extends ConsumerStatefulWidget {
  const NotificacoesScreen({super.key});

  @override
  ConsumerState<NotificacoesScreen> createState() => _NotificacoesScreenState();
}

class _NotificacoesScreenState extends ConsumerState<NotificacoesScreen> {
  Timer? _timer;
  bool _marcandoTodas = false;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(
      const Duration(seconds: 30),
      (_) => ref.invalidate(notificacoesProvider),
    );
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(notificacoesProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notificações'),
        actions: [
          if ((state.valueOrNull?.naoLidas ?? 0) > 0)
            TextButton(
              onPressed: _marcandoTodas ? null : _marcarTodas,
              child: const Text('Marcar todas'),
            ),
        ],
      ),
      body: state.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => CompanyError(
          error: error,
          onRetry: () => ref.invalidate(notificacoesProvider),
        ),
        data: (pagina) => RefreshIndicator(
          onRefresh: () => ref.refresh(notificacoesProvider.future),
          child: pagina.itens.isEmpty
              ? ListView(
                  children: const [
                    SizedBox(height: 120),
                    CompanyEmpty(message: 'Nenhuma notificação recebida.'),
                  ],
                )
              : ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  itemCount: pagina.itens.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) => _NotificacaoTile(
                    notificacao: pagina.itens[index],
                    onTap: () => _abrir(pagina.itens[index]),
                  ),
                ),
        ),
      ),
    );
  }

  Future<void> _marcarTodas() async {
    setState(() => _marcandoTodas = true);
    try {
      await ref.read(communicationRepositoryProvider).marcarNotificacoesLidas();
      ref.invalidate(notificacoesProvider);
      ref.invalidate(badgesProvider);
    } catch (error) {
      _mostrarErro(error);
    } finally {
      if (mounted) setState(() => _marcandoTodas = false);
    }
  }

  Future<void> _abrir(NotificacaoData notificacao) async {
    try {
      if (!notificacao.lida) {
        await ref
            .read(communicationRepositoryProvider)
            .marcarNotificacoesLidas(id: notificacao.id);
        ref.invalidate(notificacoesProvider);
        ref.invalidate(badgesProvider);
      }
      if (!mounted) return;
      final destino = notificacao.destino;
      if (destino != '/notificacoes') context.push(destino);
    } catch (error) {
      _mostrarErro(error);
    }
  }

  void _mostrarErro(Object error) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          error is ApiException
              ? error.mensagem
              : 'Não foi possível atualizar as notificações.',
        ),
      ),
    );
  }
}

class _NotificacaoTile extends StatelessWidget {
  const _NotificacaoTile({required this.notificacao, required this.onTap});

  final NotificacaoData notificacao;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => ColoredBox(
    color: notificacao.lida
        ? Colors.transparent
        : AppColors.secondary.withValues(alpha: 0.55),
    child: ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      onTap: onTap,
      leading: CircleAvatar(
        backgroundColor: notificacao.lida
            ? AppColors.backgroundAlt
            : AppColors.primary,
        foregroundColor: notificacao.lida ? AppColors.primary : Colors.white,
        child: Icon(_icone(notificacao.tipo)),
      ),
      title: Text(
        notificacao.titulo,
        style: TextStyle(
          fontWeight: notificacao.lida ? FontWeight.w600 : FontWeight.w800,
        ),
      ),
      subtitle: Padding(
        padding: const EdgeInsets.only(top: 4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(notificacao.mensagem),
            const SizedBox(height: 4),
            Text(
              AppFormatters.dataHoraTexto(notificacao.criadaEm),
              style: const TextStyle(fontSize: 11, color: AppColors.textLight),
            ),
          ],
        ),
      ),
      trailing: notificacao.lida
          ? const Icon(Icons.chevron_right)
          : const Icon(Icons.circle, size: 10, color: AppColors.primary),
    ),
  );

  static IconData _icone(String tipo) => switch (tipo) {
    'oportunidade' => Icons.campaign_outlined,
    'mensagem' => Icons.chat_bubble_outline,
    'agenda' => Icons.calendar_month_outlined,
    'estado' => Icons.sync_outlined,
    'pagamento' => Icons.payments_outlined,
    'mtr' => Icons.picture_as_pdf_outlined,
    _ => Icons.local_shipping_outlined,
  };
}
