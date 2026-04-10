import 'package:flutter/material.dart';
import '../theme.dart';

/// Displays three operating mode cards: Eco (0), Timed (1), Export (2).
class ModeSelector extends StatelessWidget {
  final int selected;
  final ValueChanged<int> onChanged;

  const ModeSelector({
    super.key,
    required this.selected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _ModeCard(
            index: 0,
            title: 'Eco',
            subtitle: 'Self-consumption priority',
            selected: selected == 0,
            onTap: () => onChanged(0),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _ModeCard(
            index: 1,
            title: 'Timed',
            subtitle: 'Charge/discharge on schedule',
            selected: selected == 1,
            onTap: () => onChanged(1),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _ModeCard(
            index: 2,
            title: 'Export',
            subtitle: 'Maximise grid export',
            selected: selected == 2,
            onTap: () => onChanged(2),
          ),
        ),
      ],
    );
  }
}

class _ModeCard extends StatelessWidget {
  final int index;
  final String title;
  final String subtitle;
  final bool selected;
  final VoidCallback onTap;

  const _ModeCard({
    required this.index,
    required this.title,
    required this.subtitle,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    const selectedBorder = Color(0xFF22C55E); // GivLocalColors.battery green
    const selectedBg = Color(0x1A22C55E); // green tint

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
        decoration: BoxDecoration(
          color: selected ? selectedBg : GivLocalColors.card,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: selected ? selectedBorder : GivLocalColors.cardBorder,
            width: selected ? 1.5 : 1.0,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: TextStyle(
                color: selected
                    ? selectedBorder
                    : GivLocalColors.textPrimary,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 3),
            Text(
              subtitle,
              style: const TextStyle(
                color: GivLocalColors.textMuted,
                fontSize: 10,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
