import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

/// Estrutura compartilhada das telas públicas de acesso.
class AuthLayout extends StatelessWidget {
  const AuthLayout({
    required this.title,
    required this.subtitle,
    required this.child,
    required this.footer,
    super.key,
  });

  final String title;
  final String subtitle;
  final Widget child;
  final Widget footer;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
          child: Column(
            children: [
              Container(
                width: double.infinity,
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      AppColors.primaryLight,
                      AppColors.primary,
                      AppColors.primaryDark,
                    ],
                  ),
                ),
                child: Center(
                  child: Container(
                    constraints: const BoxConstraints(maxWidth: 448),
                    padding: const EdgeInsets.fromLTRB(24, 40, 24, 64),
                    child: DefaultTextStyle(
                      style: const TextStyle(
                        fontFamily: 'Lato',
                        color: Colors.white,
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Row(
                            children: [
                              Flexible(
                                child: FittedBox(
                                  fit: BoxFit.scaleDown,
                                  child: Text(
                                    'ECOTECH',
                                    style: TextStyle(
                                      fontSize: 20,
                                      fontWeight: FontWeight.w900,
                                    ),
                                  ),
                                ),
                              ),
                              SizedBox(width: 6),
                              Icon(
                                Icons.eco_outlined,
                                color: Colors.white,
                                size: 22,
                              ),
                            ],
                          ),
                          const SizedBox(height: 32),
                          Text(
                            title,
                            style: const TextStyle(
                              fontSize: 30,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            subtitle,
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              Transform.translate(
                offset: const Offset(0, -40),
                child: Container(
                  constraints: const BoxConstraints(maxWidth: 448),
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(20),
                        decoration: BoxDecoration(
                          color: AppColors.background,
                          borderRadius: BorderRadius.circular(24),
                          border: Border.all(color: AppColors.border),
                          boxShadow: [
                            BoxShadow(
                              color: AppColors.primary.withValues(alpha: .12),
                              blurRadius: 24,
                              offset: const Offset(0, 10),
                            ),
                          ],
                        ),
                        child: child,
                      ),
                      const SizedBox(height: 16),
                      footer,
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
