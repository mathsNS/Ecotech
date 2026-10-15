import 'package:flutter/material.dart';

import '../../../core/formatters/app_formatters.dart';
import '../../../core/theme/app_colors.dart';
import '../../../data/citizen/citizen_data.dart';

class CollectionPointCard extends StatelessWidget {
  const CollectionPointCard({
    required this.point,
    required this.onSelect,
    this.selected = false,
    super.key,
  });

  final PontoColetaData point;
  final VoidCallback onSelect;
  final bool selected;

  @override
  Widget build(BuildContext context) => Card(
    margin: const EdgeInsets.only(bottom: 16),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(24),
      side: BorderSide(color: selected ? AppColors.primary : AppColors.border),
    ),
    child: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(point.nome, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 4),
          Text(point.empresa),
          const SizedBox(height: 16),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Icon(
                Icons.location_on_outlined,
                size: 18,
                color: AppColors.textLight,
              ),
              const SizedBox(width: 6),
              Expanded(child: Text(point.endereco)),
            ],
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 12,
            runSpacing: 6,
            children: [
              Text(
                '${AppFormatters.numero(point.ocupacaoKg)} / ${AppFormatters.numero(point.capacidadeKg)} kg',
              ),
              Text(
                '${AppFormatters.numero(point.capacidadeKg > 0 ? point.disponibilidadePercentual.clamp(0, 100).toDouble() : 0)}% livre',
                style: const TextStyle(
                  color: AppColors.primary,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          LinearProgressIndicator(
            value: point.capacidadeKg > 0
                ? (1 - point.ocupacaoKg / point.capacidadeKg)
                      .clamp(0, 1)
                      .toDouble()
                : 0,
            minHeight: 8,
            borderRadius: BorderRadius.circular(8),
            backgroundColor: AppColors.secondary,
            semanticsLabel: 'Capacidade livre',
          ),
          const SizedBox(height: 16),
          Text(
            point.aceitaEntrega
                ? 'Disponível para entrega'
                : 'Sem capacidade disponível',
            style: TextStyle(
              color: point.aceitaEntrega
                  ? AppColors.primary
                  : AppColors.textLight,
            ),
          ),
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: point.aceitaEntrega ? onSelect : null,
              child: Text(selected ? 'Manter este ponto' : 'Selecionar ponto'),
            ),
          ),
        ],
      ),
    ),
  );
}
