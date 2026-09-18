import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/api/api_exception.dart';
import '../../core/formatters/app_formatters.dart';
import '../../core/theme/app_colors.dart';
import '../../data/profile/perfil_data.dart';
import '../auth/auth_controller.dart';
import '../dashboard/dashboard_controller.dart';
import '../citizen/widgets/citizen_navigation.dart';
import '../company/widgets/company_navigation.dart';
import 'perfil_controller.dart';

class PerfilScreen extends ConsumerStatefulWidget {
  const PerfilScreen({super.key});

  @override
  ConsumerState<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends ConsumerState<PerfilScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nome = TextEditingController();
  final _email = TextEditingController();
  final _senhaAtual = TextEditingController();
  final _novaSenha = TextEditingController();
  final _confirmaSenha = TextEditingController();
  bool _editando = false;
  bool _dadosPreenchidos = false;

  @override
  void dispose() {
    _nome.dispose();
    _email.dispose();
    _senhaAtual.dispose();
    _novaSenha.dispose();
    _confirmaSenha.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final estado = ref.watch(perfilControllerProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Meu perfil'),
        leading: IconButton(
          tooltip: 'Voltar',
          onPressed: () => context.go('/home'),
          icon: const Icon(Icons.arrow_back),
        ),
      ),
      body: estado.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (erro, _) => _ErroPerfil(
          mensagem: erro is ApiException
              ? erro.mensagem
              : 'Não foi possível carregar o perfil.',
          onRetry: () =>
              ref.read(perfilControllerProvider.notifier).recarregar(),
        ),
        data: (perfil) {
          _preencher(perfil);
          return RefreshIndicator(
            onRefresh: () =>
                ref.read(perfilControllerProvider.notifier).recarregar(),
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 20, 16, 32),
              children: [
                Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 720),
                    child: Column(
                      children: [
                        _CabecalhoPerfil(perfil),
                        const SizedBox(height: 16),
                        _ResumoPerfil(perfil),
                        if (perfil.usuario.tipo == 'cidadao') ...[
                          const SizedBox(height: 16),
                          _ProgressoCidadao(perfil),
                        ],
                        const SizedBox(height: 16),
                        _DadosCadastrais(perfil),
                        const SizedBox(height: 16),
                        if (_editando)
                          _FormularioEdicao(
                            formKey: _formKey,
                            nome: _nome,
                            email: _email,
                            senhaAtual: _senhaAtual,
                            novaSenha: _novaSenha,
                            confirmaSenha: _confirmaSenha,
                            onCancelar: () => setState(() => _editando = false),
                            onSalvar: _salvar,
                          )
                        else
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton.icon(
                              onPressed: () => setState(() => _editando = true),
                              icon: const Icon(Icons.edit_outlined),
                              label: const Text('Editar perfil'),
                            ),
                          ),
                        const SizedBox(height: 10),
                        SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed: _logout,
                            icon: const Icon(Icons.logout),
                            label: const Text('Sair da conta'),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
      bottomNavigationBar: switch (estado.valueOrNull?.usuario.tipo) {
        'cidadao' => const CitizenNavigation(selectedIndex: 3),
        'empresa' => const CompanyNavigation(selectedIndex: 4),
        _ => NavigationBar(
          selectedIndex: 1,
          onDestinationSelected: (indice) {
            if (indice == 0) context.go('/home');
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

  void _preencher(PerfilData perfil) {
    if (_dadosPreenchidos) return;
    _nome.text = perfil.usuario.nome;
    _email.text = perfil.usuario.email ?? '';
    _dadosPreenchidos = true;
  }

  Future<void> _salvar() async {
    if (!_formKey.currentState!.validate()) return;
    final perfil = await ref
        .read(perfilControllerProvider.notifier)
        .salvar(
          nome: _nome.text.trim(),
          email: _email.text.trim(),
          senhaAtual: _senhaAtual.text,
          novaSenha: _novaSenha.text,
          confirmaSenha: _confirmaSenha.text,
        );
    if (!mounted) return;
    if (perfil != null) {
      ref
          .read(authControllerProvider.notifier)
          .atualizarUsuario(perfil.usuario);
      ref.invalidate(dashboardControllerProvider);
      _senhaAtual.clear();
      _novaSenha.clear();
      _confirmaSenha.clear();
      setState(() => _editando = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Perfil atualizado com sucesso.')),
      );
    }
  }

  Future<void> _logout() async {
    await ref.read(authControllerProvider.notifier).logout();
    ref.invalidate(dashboardControllerProvider);
    ref.invalidate(perfilControllerProvider);
    if (mounted) context.go('/login');
  }
}

class _CabecalhoPerfil extends StatelessWidget {
  const _CabecalhoPerfil(this.perfil);
  final PerfilData perfil;
  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Image.asset(
            'assets/images/icone perfil base.png',
            width: 88,
            height: 88,
          ),
          const SizedBox(height: 12),
          Text(
            perfil.usuario.nome,
            style: Theme.of(context).textTheme.titleLarge,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            _tipo(perfil.usuario.tipo),
            style: Theme.of(context).textTheme.bodyMedium,
          ),
        ],
      ),
    ),
  );

  String _tipo(String tipo) => switch (tipo) {
    'cidadao' => 'Cidadão',
    'empresa' => 'Empresa',
    'administrador' => 'Administrador',
    _ => tipo,
  };
}

class _ResumoPerfil extends StatelessWidget {
  const _ResumoPerfil(this.perfil);
  final PerfilData perfil;
  @override
  Widget build(BuildContext context) {
    final resumo = perfil.resumo;
    return Row(
      children: [
        Expanded(
          child: _ResumoItem(
            '${resumo['total_solicitacoes'] ?? 0}',
            'Solicitações',
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _ResumoItem('${resumo['finalizadas'] ?? 0}', 'Finalizadas'),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _ResumoItem(
            '${AppFormatters.numero(resumo['peso_total_kg'])} kg',
            'Peso total',
          ),
        ),
      ],
    );
  }
}

class _ResumoItem extends StatelessWidget {
  const _ResumoItem(this.valor, this.rotulo);
  final String valor;
  final String rotulo;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 16),
    decoration: BoxDecoration(
      color: AppColors.secondary,
      borderRadius: BorderRadius.circular(12),
    ),
    child: Column(
      children: [
        Text(
          valor,
          style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 4),
        Text(
          rotulo,
          style: const TextStyle(color: AppColors.textLight, fontSize: 11),
          textAlign: TextAlign.center,
        ),
      ],
    ),
  );
}

class _ProgressoCidadao extends StatelessWidget {
  const _ProgressoCidadao(this.perfil);
  final PerfilData perfil;
  @override
  Widget build(BuildContext context) {
    final resumo = perfil.resumo;
    final tier = Map<String, dynamic>.from(resumo['tier'] as Map? ?? const {});
    final conquistas = (resumo['conquistas'] as List? ?? const []);
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Progresso', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            Row(
              children: [
                Image.asset('assets/images/medalha.png', width: 30),
                const SizedBox(width: 10),
                Text(
                  '${resumo['rank'] ?? 1}º no ranking',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
                const Spacer(),
                Text('${resumo['pontos'] ?? 0} pontos'),
              ],
            ),
            const SizedBox(height: 14),
            Text('Tier ${tier['nome'] ?? 'Bronze'}'),
            const SizedBox(height: 6),
            LinearProgressIndicator(
              value: ((tier['progresso_pct'] as num?)?.toDouble() ?? 0) / 100,
              minHeight: 8,
              borderRadius: BorderRadius.circular(8),
            ),
            const SizedBox(height: 18),
            Text('Conquistas', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: conquistas.map((item) {
                final conquista = Map<String, dynamic>.from(item as Map);
                final ativa = conquista['conquistada'] == true;
                return Chip(
                  avatar: Image.asset(
                    ativa
                        ? 'assets/images/medalha.png'
                        : 'assets/images/icon-pendente.png',
                    width: 20,
                  ),
                  label: Text(conquista['titulo'] as String? ?? ''),
                  backgroundColor: ativa
                      ? AppColors.secondary
                      : AppColors.backgroundAlt,
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }
}

class _DadosCadastrais extends StatelessWidget {
  const _DadosCadastrais(this.perfil);
  final PerfilData perfil;
  @override
  Widget build(BuildContext context) {
    final campos = <MapEntry<String, String>>[
      MapEntry('Nome', perfil.usuario.nome),
      MapEntry('E-mail', perfil.usuario.email ?? ''),
      if (perfil.cpf != null) MapEntry('CPF', perfil.cpf!),
      if (perfil.cnpj != null) MapEntry('CNPJ', perfil.cnpj!),
      if (perfil.razaoSocial != null)
        MapEntry('Razão social', perfil.razaoSocial!),
      if (perfil.dataCadastro != null)
        MapEntry('Cadastro', AppFormatters.dataTexto(perfil.dataCadastro!)),
    ];
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Dados cadastrais',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 10),
            ...campos.map(
              (campo) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 7),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 105,
                      child: Text(
                        campo.key,
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ),
                    Expanded(
                      child: Text(
                        campo.value,
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FormularioEdicao extends StatelessWidget {
  const _FormularioEdicao({
    required this.formKey,
    required this.nome,
    required this.email,
    required this.senhaAtual,
    required this.novaSenha,
    required this.confirmaSenha,
    required this.onCancelar,
    required this.onSalvar,
  });
  final GlobalKey<FormState> formKey;
  final TextEditingController nome;
  final TextEditingController email;
  final TextEditingController senhaAtual;
  final TextEditingController novaSenha;
  final TextEditingController confirmaSenha;
  final VoidCallback onCancelar;
  final VoidCallback onSalvar;

  @override
  Widget build(BuildContext context) => Card(
    margin: EdgeInsets.zero,
    child: Padding(
      padding: const EdgeInsets.all(18),
      child: Form(
        key: formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Editar perfil',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: nome,
              decoration: const InputDecoration(labelText: 'Nome'),
              validator: (v) => (v?.trim().length ?? 0) < 3
                  ? 'Informe um nome válido.'
                  : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: email,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(labelText: 'E-mail'),
              validator: (v) => !(v?.contains('@') ?? false)
                  ? 'Informe um e-mail válido.'
                  : null,
            ),
            const SizedBox(height: 18),
            Text(
              'Alterar senha',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(
              'Deixe estes campos vazios para manter a senha atual.',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: senhaAtual,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Senha atual'),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: novaSenha,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Nova senha'),
              validator: (v) => v != null && v.isNotEmpty && v.length < 6
                  ? 'Use pelo menos 6 caracteres.'
                  : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: confirmaSenha,
              obscureText: true,
              decoration: const InputDecoration(
                labelText: 'Confirmar nova senha',
              ),
              validator: (v) =>
                  v != novaSenha.text ? 'As senhas não coincidem.' : null,
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: onCancelar,
                    child: const Text('Cancelar'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton(
                    onPressed: onSalvar,
                    child: const Text('Salvar'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    ),
  );
}

class _ErroPerfil extends StatelessWidget {
  const _ErroPerfil({required this.mensagem, required this.onRetry});
  final String mensagem;
  final VoidCallback onRetry;
  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(mensagem, textAlign: TextAlign.center),
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
