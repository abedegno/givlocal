import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../providers/analytics_provider.dart';
import '../providers/live_data_provider.dart';
import '../theme.dart';
import '../widgets/power_chart.dart';

class AnalyticsScreen extends ConsumerWidget {
  const AnalyticsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedDate = ref.watch(selectedDateProvider);
    final dataPointsAsync = ref.watch(dataPointsProvider);
    final liveData = ref.watch(liveDataProvider);
    final meter = liveData.meter;

    final dateLabel = DateFormat('EEEE, d MMM yyyy').format(selectedDate);
    final today = DateTime.now();
    final isToday = selectedDate.year == today.year &&
        selectedDate.month == today.month &&
        selectedDate.day == today.day;

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Text(
              'Analytics',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 16),

            // Date navigation
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                IconButton(
                  icon: const Icon(Icons.chevron_left,
                      color: GivLocalColors.textSecondary),
                  onPressed: () {
                    ref.read(selectedDateProvider.notifier).state =
                        selectedDate.subtract(const Duration(days: 1));
                  },
                ),
                Text(
                  dateLabel,
                  style: const TextStyle(
                    color: GivLocalColors.textPrimary,
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                IconButton(
                  icon: Icon(
                    Icons.chevron_right,
                    color: isToday
                        ? GivLocalColors.textMuted
                        : GivLocalColors.textSecondary,
                  ),
                  onPressed: isToday
                      ? null
                      : () {
                          ref.read(selectedDateProvider.notifier).state =
                              selectedDate.add(const Duration(days: 1));
                        },
                ),
              ],
            ),
            const SizedBox(height: 12),

            // Chart card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: GivLocalColors.card,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: GivLocalColors.cardBorder),
              ),
              child: dataPointsAsync.when(
                data: (points) => PowerChart(dataPoints: points),
                loading: () => const SizedBox(
                  height: 200,
                  child: Center(child: CircularProgressIndicator()),
                ),
                error: (_, __) => const SizedBox(
                  height: 200,
                  child: Center(
                    child: Text(
                      'Failed to load chart data',
                      style: TextStyle(color: GivLocalColors.textMuted),
                    ),
                  ),
                ),
              ),
            ),

            // Legend
            const SizedBox(height: 12),
            _ChartLegend(),

            const SizedBox(height: 20),

            // Energy today section
            const Text(
              'ENERGY TODAY',
              style: TextStyle(
                color: GivLocalColors.textMuted,
                fontSize: 11,
                fontWeight: FontWeight.w600,
                letterSpacing: 1.0,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              decoration: BoxDecoration(
                color: GivLocalColors.card,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: GivLocalColors.cardBorder),
              ),
              child: meter == null
                  ? const Padding(
                      padding: EdgeInsets.all(16),
                      child: Center(
                        child: Text(
                          'Loading energy data…',
                          style: TextStyle(color: GivLocalColors.textSecondary),
                        ),
                      ),
                    )
                  : Column(
                      children: [
                        _EnergyRow(
                          color: GivLocalColors.solar,
                          label: 'Solar Generated',
                          kwh: meter.today.solar,
                        ),
                        _Divider(),
                        _EnergyRow(
                          color: GivLocalColors.home,
                          label: 'Home Consumed',
                          kwh: meter.today.consumption,
                        ),
                        _Divider(),
                        _EnergyRow(
                          color: GivLocalColors.battery,
                          label: 'Grid Export',
                          kwh: meter.today.gridExport,
                        ),
                        _Divider(),
                        _EnergyRow(
                          color: GivLocalColors.grid,
                          label: 'Grid Import',
                          kwh: meter.today.gridImport,
                        ),
                        _Divider(),
                        _EnergyRow(
                          color: GivLocalColors.battery,
                          label: 'Battery Charge',
                          kwh: meter.today.batteryCharge,
                        ),
                        _Divider(),
                        _EnergyRow(
                          color: GivLocalColors.battery,
                          label: 'Battery Discharge',
                          kwh: meter.today.batteryDischarge,
                        ),
                      ],
                    ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}

class _ChartLegend extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 16,
      runSpacing: 6,
      children: const [
        _LegendItem(color: GivLocalColors.solar, label: 'Solar'),
        _LegendItem(color: GivLocalColors.battery, label: 'Battery'),
        _LegendItem(color: GivLocalColors.grid, label: 'Grid'),
        _LegendItem(color: GivLocalColors.home, label: 'Consumption'),
      ],
    );
  }
}

class _LegendItem extends StatelessWidget {
  final Color color;
  final String label;

  const _LegendItem({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
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

class _EnergyRow extends StatelessWidget {
  final Color color;
  final String label;
  final double kwh;

  const _EnergyRow({
    required this.color,
    required this.label,
    required this.kwh,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          Container(
            width: 10,
            height: 10,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(
                color: GivLocalColors.textPrimary,
                fontSize: 14,
              ),
            ),
          ),
          Text(
            '${kwh.toStringAsFixed(1)} kWh',
            style: TextStyle(
              color: color,
              fontSize: 14,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}

class _Divider extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return const Divider(
      height: 1,
      thickness: 1,
      indent: 16,
      endIndent: 16,
      color: GivLocalColors.cardBorder,
    );
  }
}
