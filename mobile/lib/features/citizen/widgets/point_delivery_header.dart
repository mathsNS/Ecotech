import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../../data/citizen/citizen_data.dart';
import 'collection_fields.dart';

class PointDeliveryHeader extends StatelessWidget {
  const PointDeliveryHeader({
    required this.point,
    required this.scheduling,
    super.key,
  });
  final PontoColetaData point;
  final bool scheduling;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          gradient: const LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [AppColors.primaryLight, AppColors.primaryDark],
          ),
        ),
        child: DefaultTextStyle(
          style: const TextStyle(color: Colors.white, fontSize: 14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'PONTO SELECIONADO',
                style: TextStyle(fontSize: 11, fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 8),
              Text(
                point.nome,
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 4),
              Text(point.empresa),
              const SizedBox(height: 16),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(
                    Icons.location_on_outlined,
                    size: 18,
                    color: Colors.white,
                  ),
                  const SizedBox(width: 6),
                  Expanded(child: Text(point.endereco)),
                ],
              ),
              if (!point.aceitaEntrega) ...[
                const SizedBox(height: 12),
                const Text(
                  'Este ponto está sem capacidade. Escolha outro para continuar.',
                ),
              ],
            ],
          ),
        ),
      ),
      const SizedBox(height: 20),
      CollectionPair(
        first: _step('1 · Seu item', !scheduling),
        second: _step('2 · Horário', scheduling),
      ),
    ],
  );

  Widget _step(String label, bool active) => Semantics(
    selected: active,
    child: Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: active ? AppColors.secondary : Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: active ? AppColors.primary : AppColors.border,
        ),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: AppColors.primaryDark,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
  );
}
