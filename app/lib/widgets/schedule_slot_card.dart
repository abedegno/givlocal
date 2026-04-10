import 'package:flutter/material.dart';
import '../theme.dart';

/// Card showing a single charge or discharge slot.
class ScheduleSlotCard extends StatelessWidget {
  final int slotNumber;
  final String startTime;
  final String endTime;
  final int targetSoc;
  final bool enabled;
  final ValueChanged<bool> onToggle;

  const ScheduleSlotCard({
    super.key,
    required this.slotNumber,
    required this.startTime,
    required this.endTime,
    required this.targetSoc,
    required this.enabled,
    required this.onToggle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: GivLocalColors.card,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: GivLocalColors.cardBorder),
      ),
      child: Row(
        children: [
          // Slot number badge
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              color: const Color(0x1A818CF8), // accent tint
              borderRadius: BorderRadius.circular(6),
              border: Border.all(color: const Color(0x40818CF8)),
            ),
            alignment: Alignment.center,
            child: Text(
              '$slotNumber',
              style: const TextStyle(
                color: GivLocalColors.accent,
                fontSize: 13,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          const SizedBox(width: 12),

          // Time range
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$startTime – $endTime',
                  style: const TextStyle(
                    color: GivLocalColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  'Target: $targetSoc%',
                  style: const TextStyle(
                    color: GivLocalColors.textSecondary,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),

          // Enable/disable switch
          Switch(
            value: enabled,
            onChanged: onToggle,
            activeColor: GivLocalColors.battery,
            inactiveTrackColor: const Color(0x33FFFFFF),
            inactiveThumbColor: GivLocalColors.textMuted,
          ),
        ],
      ),
    );
  }
}
