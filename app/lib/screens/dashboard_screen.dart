import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/live_data_provider.dart';
import '../theme.dart';
import '../widgets/connection_indicator.dart';
import '../widgets/energy_flow_diagram.dart';

String _formatKwh(double kwh) {
  return '${kwh.toStringAsFixed(1)} kWh';
}

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final liveData = ref.watch(liveDataProvider);
    final system = liveData.system;
    final meter = liveData.meter;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Dashboard',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const ConnectionIndicator(),
              ],
            ),
            const SizedBox(height: 16),

            // Energy flow diagram
            Expanded(
              flex: 5,
              child: system == null
                  ? Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const SizedBox(height: 40),
                          Icon(Icons.bolt, size: 48, color: GivLocalColors.textMuted.withAlpha(80)),
                          const SizedBox(height: 16),
                          Text('Connecting to inverter...', style: TextStyle(color: GivLocalColors.textMuted)),
                        ],
                      ),
                    )
                  : EnergyFlowDiagram(data: system),
            ),

            const SizedBox(height: 16),

            // Today's summary card
            _SummaryCard(meter: meter),

            const SizedBox(height: 12),

            // Quick status
            if (system != null) _QuickStatus(system: system),
          ],
        ),
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final dynamic meter;

  const _SummaryCard({required this.meter});

  @override
  Widget build(BuildContext context) {
    if (meter == null) {
      return Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: GivLocalColors.card,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: GivLocalColors.cardBorder),
        ),
        child: const Center(
          child: Text(
            'Loading today\'s summary…',
            style: TextStyle(color: GivLocalColors.textSecondary),
          ),
        ),
      );
    }

    final today = meter.today;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: GivLocalColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: GivLocalColors.cardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Today',
            style: TextStyle(
              color: GivLocalColors.textSecondary,
              fontSize: 13,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _SummaryItem(
                icon: Icons.wb_sunny,
                color: GivLocalColors.solar,
                label: 'Solar',
                value: _formatKwh(today.solar),
              ),
              _SummaryItem(
                icon: Icons.home,
                color: GivLocalColors.home,
                label: 'Consumed',
                value: _formatKwh(today.consumption),
              ),
              _SummaryItem(
                icon: Icons.upload,
                color: GivLocalColors.grid,
                label: 'Export',
                value: _formatKwh(today.gridExport),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SummaryItem extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String label;
  final String value;

  const _SummaryItem({
    required this.icon,
    required this.color,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, color: color, size: 20),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(
            color: GivLocalColors.textPrimary,
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        Text(
          label,
          style: const TextStyle(
            color: GivLocalColors.textMuted,
            fontSize: 11,
          ),
        ),
      ],
    );
  }
}

class _QuickStatus extends StatelessWidget {
  final dynamic system;

  const _QuickStatus({required this.system});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: GivLocalColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: GivLocalColors.cardBorder),
      ),
      child: Row(
        children: [
          const Icon(Icons.info_outline,
              color: GivLocalColors.textMuted, size: 16),
          const SizedBox(width: 8),
          Text(
            'Status: ${system.status.isNotEmpty ? system.status : "Unknown"}',
            style: const TextStyle(
              color: GivLocalColors.textSecondary,
              fontSize: 12,
            ),
          ),
          const Spacer(),
          Text(
            'Bat: ${system.battery.percent}%',
            style: const TextStyle(
              color: GivLocalColors.textMuted,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}
