import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

enum AuthRole {
  cidadao('Cidadão', Icons.person_outline),
  empresa('Empresa', Icons.business_outlined),
  administrador('Admin', Icons.shield_outlined);

  const AuthRole(this.label, this.icon);
  final String label;
  final IconData icon;
}

class AuthRoleSelector extends StatelessWidget {
  const AuthRoleSelector({
    required this.roles,
    required this.value,
    required this.onChanged,
    super.key,
  });

  final List<AuthRole> roles;
  final AuthRole value;
  final ValueChanged<AuthRole>? onChanged;

  @override
  Widget build(BuildContext context) {
    final vertical = MediaQuery.textScalerOf(context).scale(14) > 20;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: AppColors.surfaceSubtle,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Padding(
        padding: const EdgeInsets.all(4),
        child: LayoutBuilder(
          builder: (context, constraints) {
            final buttons = roles.map((role) {
              final selected = value == role;
              return Semantics(
                selected: selected,
                inMutuallyExclusiveGroup: true,
                child: TextButton(
                  onPressed: onChanged == null ? null : () => onChanged!(role),
                  style: TextButton.styleFrom(
                    minimumSize: const Size(48, 48),
                    padding: const EdgeInsets.symmetric(
                      horizontal: 6,
                      vertical: 10,
                    ),
                    backgroundColor: selected
                        ? AppColors.background
                        : Colors.transparent,
                    foregroundColor: selected
                        ? AppColors.primary
                        : AppColors.textLight,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (vertical ||
                          constraints.maxWidth / roles.length >= 92) ...[
                        Icon(role.icon, size: 16),
                        const SizedBox(width: 6),
                      ],
                      Flexible(
                        child: Text(
                          role.label,
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontWeight: FontWeight.w900),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }).toList();
            return vertical
                ? Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: buttons,
                  )
                : Row(
                    children: [
                      for (final button in buttons) Expanded(child: button),
                    ],
                  );
          },
        ),
      ),
    );
  }
}
