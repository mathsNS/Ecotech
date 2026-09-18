import 'package:flutter/material.dart';

const operationsBackground = Color(0xFFF7F8F9);
const operationsBorder = Color(0xFFE5E9E7);
const operationsMuted = Color(0xFF606870);
const operationsDark = Color(0xFF111315);
const operationsSoftGreen = Color(0xFFE2F2E8);
const operationsDeepGreen = Color(0xFF1F603E);

class OperationsMetric extends StatelessWidget {
  const OperationsMetric({
    required this.icon,
    required this.value,
    required this.label,
    super.key,
  });

  final IconData icon;
  final int value;
  final String label;

  @override
  Widget build(BuildContext context) => Container(
    height: 133,
    padding: const EdgeInsets.fromLTRB(16, 17, 12, 15),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(20),
      border: Border.all(color: operationsBorder),
      boxShadow: const [
        BoxShadow(
          color: Color(0x0D000000),
          blurRadius: 3,
          offset: Offset(0, 2),
        ),
      ],
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 40,
          height: 40,
          decoration: const BoxDecoration(
            color: operationsSoftGreen,
            shape: BoxShape.circle,
          ),
          child: Icon(icon, size: 21, color: operationsDeepGreen),
        ),
        const Spacer(),
        Text(
          '$value',
          style: const TextStyle(
            fontSize: 24,
            height: 1,
            fontWeight: FontWeight.w700,
            color: operationsDark,
          ),
        ),
        const SizedBox(height: 7),
        Text(
          label,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontSize: 10.5, color: operationsMuted),
        ),
      ],
    ),
  );
}

class OperationsFilters extends StatelessWidget {
  const OperationsFilters({
    required this.selected,
    required this.onSelected,
    super.key,
  });

  final String selected;
  final ValueChanged<String> onSelected;

  static const filters = <(String, String)>[
    ('Todos os estados', ''),
    ('Solicitado', 'Solicitado'),
    ('Coletado', 'Coletado'),
    ('Em processamento', 'Em Processamento'),
    ('Reciclado', 'Reciclado'),
    ('Reutilizado', 'Reutilizado'),
    ('Descartado', 'Descartado'),
    ('Cancelado', 'Cancelado'),
  ];

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const Row(
        children: [
          Icon(Icons.filter_alt_outlined, size: 19, color: operationsMuted),
          SizedBox(width: 7),
          Text(
            'Filtrar por estado',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: operationsDark,
            ),
          ),
        ],
      ),
      const SizedBox(height: 10),
      SizedBox(
        height: 34,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemCount: filters.length,
          separatorBuilder: (_, _) => const SizedBox(width: 8),
          itemBuilder: (context, index) {
            final filter = filters[index];
            final active = selected == filter.$2;
            return ChoiceChip(
              label: Text(filter.$1),
              selected: active,
              onSelected: (_) => onSelected(filter.$2),
              showCheckmark: false,
              side: BorderSide(
                color: active ? operationsDeepGreen : operationsBorder,
              ),
              backgroundColor: Colors.white,
              selectedColor: const Color(0xFF327B58),
              labelStyle: TextStyle(
                color: active ? Colors.white : operationsMuted,
                fontSize: 10.5,
                fontWeight: FontWeight.w600,
              ),
              padding: const EdgeInsets.symmetric(horizontal: 5),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(18),
              ),
            );
          },
        ),
      ),
    ],
  );
}

class OperationsSectionTitle extends StatelessWidget {
  const OperationsSectionTitle({required this.total, super.key});

  final int total;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      const Expanded(
        child: Text(
          'Solicitações',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w700,
            color: operationsDark,
          ),
        ),
      ),
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: const Color(0xFFE7F1EC),
          borderRadius: BorderRadius.circular(18),
        ),
        child: Text(
          '$total encontradas',
          style: const TextStyle(
            color: operationsDeepGreen,
            fontSize: 10,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    ],
  );
}

class OperationsStatus extends StatelessWidget {
  const OperationsStatus(this.status, {super.key});

  final String status;

  @override
  Widget build(BuildContext context) {
    final normalized = status.toLowerCase().replaceAll('_', ' ');
    final processing = normalized.contains('processamento');
    final collected = normalized == 'coletado';
    final cancelled = normalized == 'cancelado';
    final color = cancelled
        ? const Color(0xFF9F3030)
        : collected || processing
        ? const Color(0xFF7A5200)
        : const Color(0xFF23774E);
    final background = cancelled
        ? const Color(0xFFFBE4E4)
        : collected || processing
        ? const Color(0xFFFFF0C9)
        : const Color(0xFFE3F1EA);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 4),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Text(
        status.replaceAll('_', ' ').toUpperCase(),
        maxLines: 1,
        style: TextStyle(
          color: color,
          fontSize: 9,
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}

class OperationsCard extends StatelessWidget {
  const OperationsCard({
    required this.title,
    required this.subtitle,
    required this.status,
    required this.weight,
    required this.date,
    required this.shortId,
    required this.onDetails,
    this.onSchedule,
    this.onChat,
    super.key,
  });

  final String title;
  final String subtitle;
  final String status;
  final String weight;
  final String date;
  final String shortId;
  final VoidCallback onDetails;
  final VoidCallback? onSchedule;
  final VoidCallback? onChat;

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 11),
    padding: const EdgeInsets.fromLTRB(15, 14, 15, 14),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(20),
      border: Border.all(color: operationsBorder),
      boxShadow: const [
        BoxShadow(
          color: Color(0x0E000000),
          blurRadius: 3,
          offset: Offset(0, 2),
        ),
      ],
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                title,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 15.5,
                  fontWeight: FontWeight.w700,
                  color: operationsDark,
                ),
              ),
            ),
            const SizedBox(width: 8),
            OperationsStatus(status),
          ],
        ),
        const SizedBox(height: 7),
        Text(
          subtitle,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: const TextStyle(fontSize: 11.5, color: operationsMuted),
        ),
        const SizedBox(height: 11),
        Row(
          children: [
            const Icon(
              Icons.balance_outlined,
              size: 14,
              color: Color(0xFF277550),
            ),
            const SizedBox(width: 5),
            Text(
              weight,
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
            ),
            const SizedBox(width: 14),
            const Icon(
              Icons.calendar_month_outlined,
              size: 14,
              color: operationsMuted,
            ),
            const SizedBox(width: 5),
            Text(
              date,
              style: const TextStyle(fontSize: 10.5, color: operationsMuted),
            ),
            const Spacer(),
            Flexible(
              child: Text(
                '$shortId...',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 9.5,
                  letterSpacing: .4,
                  color: Color(0xFF90979D),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 13),
        Row(
          children: [
            Expanded(
              child: SizedBox(
                height: 41,
                child: FilledButton.icon(
                  onPressed: onDetails,
                  icon: const Icon(Icons.visibility_outlined, size: 17),
                  label: const Text(
                    'Ver Detalhes',
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                  ),
                  style: FilledButton.styleFrom(
                    backgroundColor: operationsDeepGreen,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(11),
                    ),
                  ),
                ),
              ),
            ),
            if (onSchedule != null) ...[
              const SizedBox(width: 8),
              _CardAction(
                icon: Icons.calendar_month_outlined,
                label: 'Abrir agenda',
                onTap: onSchedule!,
              ),
            ],
            if (onChat != null) ...[
              const SizedBox(width: 8),
              _CardAction(
                icon: Icons.chat_bubble_outline_rounded,
                label: 'Abrir conversa',
                onTap: onChat!,
              ),
            ],
          ],
        ),
      ],
    ),
  );
}

class _CardAction extends StatelessWidget {
  const _CardAction({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Semantics(
    button: true,
    label: label,
    child: Material(
      color: operationsSoftGreen,
      borderRadius: BorderRadius.circular(11),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(11),
        child: SizedBox(
          width: 40,
          height: 41,
          child: Icon(icon, size: 19, color: operationsDeepGreen),
        ),
      ),
    ),
  );
}

class OperationsPagination extends StatelessWidget {
  const OperationsPagination({
    required this.page,
    required this.totalPages,
    this.onPrevious,
    this.onNext,
    super.key,
  });

  final int page;
  final int totalPages;
  final VoidCallback? onPrevious;
  final VoidCallback? onNext;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 4),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        IconButton(onPressed: onPrevious, icon: const Icon(Icons.chevron_left)),
        Text(
          '$page de $totalPages',
          style: const TextStyle(fontSize: 12, color: operationsMuted),
        ),
        IconButton(onPressed: onNext, icon: const Icon(Icons.chevron_right)),
      ],
    ),
  );
}
