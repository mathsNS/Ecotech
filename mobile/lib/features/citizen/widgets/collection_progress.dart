import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';

class CollectionProgress extends StatelessWidget {
  const CollectionProgress({
    required this.step,
    required this.atCollectionPoint,
    super.key,
  });

  final int step;
  final bool atCollectionPoint;

  @override
  Widget build(BuildContext context) {
    final labels = [
      'Dispositivo',
      atCollectionPoint ? 'Ponto de coleta' : 'Endereço',
      'Agendamento',
    ];
    final descriptions = [
      'Preencha as informações sobre o dispositivo que deseja descartar.',
      atCollectionPoint
          ? 'Escolha onde entregar o dispositivo e informe o contato.'
          : 'Informe o endereço e quem poderá receber a equipe de coleta.',
      'Escolha sua disponibilidade e revise os dados da solicitação.',
    ];
    final icons = [
      Icons.phone_android_outlined,
      atCollectionPoint ? Icons.location_on_outlined : Icons.home_outlined,
      Icons.calendar_month_outlined,
    ];
    return Column(
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
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Semantics(
                liveRegion: true,
                header: true,
                child: Text(
                  'Etapa ${step + 1} de 3 · ${labels[step]}',
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                descriptions[step],
                style: const TextStyle(color: Colors.white),
              ),
              const SizedBox(height: 20),
              Image.asset(
                'assets/images/coleta-van.png',
                height: 120,
                width: double.infinity,
                fit: BoxFit.contain,
                excludeFromSemantics: true,
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            for (var i = 0; i < labels.length; i++)
              Expanded(
                child: Semantics(
                  label:
                      'Etapa ${i + 1}: ${labels[i]}${i < step ? ', concluída' : ''}',
                  selected: i == step,
                  excludeSemantics: true,
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Divider(
                              color: i == 0
                                  ? Colors.transparent
                                  : AppColors.secondary,
                            ),
                          ),
                          CircleAvatar(
                            radius: 20,
                            backgroundColor: i <= step
                                ? AppColors.primary
                                : AppColors.surfaceSubtle,
                            foregroundColor: i <= step
                                ? Colors.white
                                : AppColors.textLight,
                            child: Icon(
                              i < step ? Icons.check : icons[i],
                              size: 21,
                            ),
                          ),
                          Expanded(
                            child: Divider(
                              color: i == 2
                                  ? Colors.transparent
                                  : AppColors.secondary,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      Text(
                        labels[i],
                        textAlign: TextAlign.center,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w700,
                          color: i <= step
                              ? AppColors.primary
                              : AppColors.textLight,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }
}
