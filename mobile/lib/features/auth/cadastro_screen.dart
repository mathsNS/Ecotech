import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import 'auth_controller.dart';
import 'widgets/auth_field.dart';
import 'widgets/auth_layout.dart';
import 'widgets/auth_role_selector.dart';

class CadastroScreen extends ConsumerStatefulWidget {
  const CadastroScreen({super.key});

  @override
  ConsumerState<CadastroScreen> createState() => _CadastroScreenState();
}

class _CadastroScreenState extends ConsumerState<CadastroScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nomeController = TextEditingController();
  final _emailController = TextEditingController();
  final _cpfController = TextEditingController();
  final _cnpjController = TextEditingController();
  final _razaoSocialController = TextEditingController();
  final _senhaController = TextEditingController();
  final _senhaConfirmacaoController = TextEditingController();
  bool _isCidadao = true;
  bool _carregando = false;

  @override
  void dispose() {
    _nomeController.dispose();
    _emailController.dispose();
    _cpfController.dispose();
    _cnpjController.dispose();
    _razaoSocialController.dispose();
    _senhaController.dispose();
    _senhaConfirmacaoController.dispose();
    super.dispose();
  }

  Future<void> _criarConta() async {
    if (_carregando || !_formKey.currentState!.validate()) return;

    setState(() => _carregando = true);
    await ref
        .read(authControllerProvider.notifier)
        .registrar(
          tipo: _isCidadao ? 'cidadao' : 'empresa',
          nome: _nomeController.text.trim(),
          email: _emailController.text.trim(),
          senha: _senhaController.text,
          senhaConfirmacao: _senhaConfirmacaoController.text,
          cpf: _isCidadao ? _cpfController.text.trim() : null,
          cnpj: _isCidadao ? null : _cnpjController.text.trim(),
          razaoSocial: _isCidadao ? null : _razaoSocialController.text.trim(),
        );
    if (!mounted) return;
    setState(() => _carregando = false);

    final estado = ref.read(authControllerProvider);
    estado.whenOrNull(
      data: (usuario) {
        if (usuario != null) context.go('/home');
      },
      error: (erro, _) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(erro.toString()),
            backgroundColor: AppColors.error,
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return AuthLayout(
      title: 'Criar conta',
      subtitle: 'Escolha como você quer fazer parte da EcoTech.',
      footer: TextButton(
        onPressed: _carregando ? null : () => context.go('/login'),
        child: const Text('Já tem uma conta? Entrar'),
      ),
      child: AutofillGroup(
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AuthRoleSelector(
                roles: const [AuthRole.cidadao, AuthRole.empresa],
                value: _isCidadao ? AuthRole.cidadao : AuthRole.empresa,
                onChanged: _carregando
                    ? null
                    : (role) =>
                          setState(() => _isCidadao = role == AuthRole.cidadao),
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.secondary,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  _isCidadao
                      ? 'Descarte eletrônicos com segurança e ganhe saldo e EcoPoints a cada entrega.'
                      : 'Receba coletas na sua região, gerencie operações e emita relatórios ambientais.',
                  style: const TextStyle(
                    color: AppColors.primaryDark,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              const SizedBox(height: 16),
              if (_isCidadao) ...[
                _campo(
                  'Nome completo',
                  _nomeController,
                  hint: 'Seu nome',
                  autofill: AutofillHints.name,
                ),
                _campo(
                  'CPF',
                  _cpfController,
                  hint: '000.000.000-00',
                  keyboard: TextInputType.number,
                ),
              ] else ...[
                _campo(
                  'Razão social',
                  _razaoSocialController,
                  hint: 'Nome jurídico da empresa',
                ),
                _campo(
                  'CNPJ',
                  _cnpjController,
                  hint: '00.000.000/0000-00',
                  keyboard: TextInputType.number,
                ),
                _campo(
                  'Nome da empresa',
                  _nomeController,
                  hint: 'Nome exibido no aplicativo',
                  autofill: AutofillHints.organizationName,
                ),
              ],
              _campo(
                'E-mail',
                _emailController,
                hint: _isCidadao ? 'voce@exemplo.com' : 'contato@empresa.com',
                keyboard: TextInputType.emailAddress,
                autofill: AutofillHints.email,
              ),
              _campo(
                'Senha',
                _senhaController,
                hint: 'Mínimo de 6 caracteres',
                password: true,
                autofill: AutofillHints.newPassword,
                validator: (valor) =>
                    _obrigatorio(valor) ??
                    (valor!.length < 6 ? 'Use pelo menos 6 caracteres' : null),
              ),
              _campo(
                'Confirmar senha',
                _senhaConfirmacaoController,
                hint: 'Repita a senha',
                password: true,
                last: true,
                autofill: AutofillHints.newPassword,
                validator: (valor) =>
                    _obrigatorio(valor) ??
                    (valor != _senhaController.text
                        ? 'As senhas não conferem'
                        : null),
              ),
              const SizedBox(height: 8),
              ElevatedButton.icon(
                onPressed: _carregando ? null : _criarConta,
                icon: _carregando
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.person_add_alt_outlined, size: 18),
                label: Text(_carregando ? 'Criando conta...' : 'Criar conta'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _campo(
    String label,
    TextEditingController controller, {
    String? hint,
    String? autofill,
    TextInputType? keyboard,
    bool password = false,
    bool last = false,
    FormFieldValidator<String>? validator,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: AuthField(
        label: '$label *',
        child: TextFormField(
          key: ValueKey(label),
          controller: controller,
          enabled: !_carregando,
          decoration: InputDecoration(hintText: hint),
          keyboardType: keyboard,
          obscureText: password,
          autocorrect: !password,
          enableSuggestions: !password,
          autofillHints: autofill == null ? null : [autofill],
          textInputAction: last ? TextInputAction.done : TextInputAction.next,
          onFieldSubmitted: last ? (_) => _criarConta() : null,
          validator: validator ?? _obrigatorio,
        ),
      ),
    );
  }

  String? _obrigatorio(String? valor) =>
      (valor == null || valor.trim().isEmpty) ? 'Campo obrigatório' : null;
}
