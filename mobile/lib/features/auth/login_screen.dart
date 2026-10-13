import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import 'auth_controller.dart';
import 'widgets/auth_field.dart';
import 'widgets/auth_layout.dart';
import 'widgets/auth_role_selector.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _credencialController = TextEditingController();
  final _senhaController = TextEditingController();
  AuthRole _tipo = AuthRole.cidadao;
  bool _carregando = false;
  bool _mostrarSenha = false;

  static const _configPorTipo = {
    AuthRole.cidadao: (label: 'CPF', hint: '000.000.000-00'),
    AuthRole.empresa: (label: 'CNPJ', hint: '00.000.000/0000-00'),
    AuthRole.administrador: (label: 'E-mail', hint: 'admin@ecotech.com'),
  };

  @override
  void dispose() {
    _credencialController.dispose();
    _senhaController.dispose();
    super.dispose();
  }

  Future<void> _entrar() async {
    if (_carregando || !_formKey.currentState!.validate()) return;

    setState(() => _carregando = true);
    await ref
        .read(authControllerProvider.notifier)
        .login(
          tipo: _tipo.name,
          credencial: _credencialController.text.trim(),
          senha: _senhaController.text,
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
    final config = _configPorTipo[_tipo]!;

    return AuthLayout(
      title: 'Que bom te ver',
      subtitle: 'Entre para continuar reciclando com impacto.',
      footer: TextButton(
        onPressed: _carregando ? null : () => context.go('/cadastro'),
        child: const Text('Não tem uma conta? Criar conta'),
      ),
      child: AutofillGroup(
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              AuthRoleSelector(
                roles: AuthRole.values,
                value: _tipo,
                onChanged: _carregando
                    ? null
                    : (tipo) => setState(() {
                        _tipo = tipo;
                        _credencialController.clear();
                        _formKey.currentState?.reset();
                      }),
              ),
              const SizedBox(height: 20),
              AuthField(
                label: config.label,
                child: TextFormField(
                  controller: _credencialController,
                  enabled: !_carregando,
                  decoration: InputDecoration(hintText: config.hint),
                  keyboardType: _tipo == AuthRole.administrador
                      ? TextInputType.emailAddress
                      : TextInputType.number,
                  textInputAction: TextInputAction.next,
                  autofillHints: const [AutofillHints.username],
                  autocorrect: false,
                  validator: (valor) => (valor == null || valor.trim().isEmpty)
                      ? 'Campo obrigatório'
                      : null,
                ),
              ),
              const SizedBox(height: 16),
              AuthField(
                label: 'Senha',
                child: TextFormField(
                  controller: _senhaController,
                  enabled: !_carregando,
                  decoration: InputDecoration(
                    hintText: 'Sua senha',
                    suffixIcon: IconButton(
                      tooltip: _mostrarSenha
                          ? 'Ocultar senha'
                          : 'Mostrar senha',
                      onPressed: _carregando
                          ? null
                          : () =>
                                setState(() => _mostrarSenha = !_mostrarSenha),
                      icon: Icon(
                        _mostrarSenha
                            ? Icons.visibility_off_outlined
                            : Icons.visibility_outlined,
                        size: 20,
                      ),
                    ),
                  ),
                  obscureText: !_mostrarSenha,
                  autocorrect: false,
                  enableSuggestions: false,
                  autofillHints: const [AutofillHints.password],
                  textInputAction: TextInputAction.done,
                  onFieldSubmitted: (_) => _entrar(),
                  validator: (valor) => (valor == null || valor.isEmpty)
                      ? 'Campo obrigatório'
                      : null,
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _carregando ? null : _entrar,
                icon: _carregando
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.login, size: 18),
                label: Text(_carregando ? 'Entrando...' : 'Entrar'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
