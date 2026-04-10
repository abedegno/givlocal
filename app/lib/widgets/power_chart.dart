import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../theme.dart';

class PowerChart extends StatelessWidget {
  final List<Map<String, dynamic>> dataPoints;

  const PowerChart({super.key, required this.dataPoints});

  @override
  Widget build(BuildContext context) {
    if (dataPoints.isEmpty) {
      return SizedBox(
        height: 220,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.bar_chart, size: 40, color: GivLocalColors.textMuted.withAlpha(80)),
              const SizedBox(height: 8),
              const Text('No data for this date', style: TextStyle(color: GivLocalColors.textMuted, fontSize: 14)),
              const SizedBox(height: 4),
              const Text('Try a date when your system was online',
                  style: TextStyle(color: GivLocalColors.textMuted, fontSize: 11)),
            ],
          ),
        ),
      );
    }

    final solarSpots = <FlSpot>[];
    final gridSpots = <FlSpot>[];
    final batterySpots = <FlSpot>[];
    final consumptionSpots = <FlSpot>[];
    final timeLabels = <int, String>{};

    for (var i = 0; i < dataPoints.length; i++) {
      final dp = dataPoints[i];
      final power = dp['power'] as Map<String, dynamic>? ?? {};
      final solar = (power['solar'] as Map<String, dynamic>?)?['power'] as num? ?? 0;
      final grid = (power['grid'] as Map<String, dynamic>?)?['power'] as num? ?? 0;
      final battery = (power['battery'] as Map<String, dynamic>?)?['power'] as num? ?? 0;
      final consumption = (power['consumption'] as Map<String, dynamic>?)?['power'] as num? ?? 0;

      final x = i.toDouble();
      solarSpots.add(FlSpot(x, solar.abs() / 1000));
      gridSpots.add(FlSpot(x, grid.abs() / 1000));
      batterySpots.add(FlSpot(x, battery.abs() / 1000));
      consumptionSpots.add(FlSpot(x, consumption.abs() / 1000));

      // Parse time for X axis labels
      final timeStr = dp['time'] as String? ?? '';
      if (timeStr.isNotEmpty) {
        try {
          final dt = DateTime.parse(timeStr);
          timeLabels[i] = '${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
        } catch (_) {}
      }
    }

    // Calculate label interval - show ~6 labels across the chart
    final labelInterval = dataPoints.length > 6 ? (dataPoints.length / 6).ceil() : 1;

    LineChartBarData series(
      List<FlSpot> spots,
      Color color, {
      List<int>? dashArray,
    }) {
      return LineChartBarData(
        spots: spots,
        isCurved: true,
        color: color,
        barWidth: 2,
        dashArray: dashArray,
        dotData: const FlDotData(show: false),
        belowBarData: BarAreaData(
          show: true,
          color: color.withAlpha(38),
        ),
      );
    }

    return Semantics(
      label: 'Power chart showing solar, battery, grid and consumption over time',
      child: SizedBox(
        height: 220,
        child: LineChart(
          LineChartData(
            gridData: FlGridData(
              show: true,
              drawVerticalLine: false,
              getDrawingHorizontalLine: (value) => FlLine(
                color: GivLocalColors.cardBorder,
                strokeWidth: 1,
              ),
            ),
            titlesData: FlTitlesData(
              topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              leftTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 36,
                  getTitlesWidget: (value, meta) {
                    return Text(
                      '${value.toStringAsFixed(0)}',
                      style: const TextStyle(color: GivLocalColors.textMuted, fontSize: 10),
                    );
                  },
                ),
              ),
              bottomTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 24,
                  interval: labelInterval.toDouble(),
                  getTitlesWidget: (value, meta) {
                    final idx = value.toInt();
                    final label = timeLabels[idx];
                    if (label == null) return const SizedBox.shrink();
                    return Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text(
                        label,
                        style: const TextStyle(color: GivLocalColors.textMuted, fontSize: 10),
                      ),
                    );
                  },
                ),
              ),
            ),
            borderData: FlBorderData(show: false),
            lineBarsData: [
              series(solarSpots, GivLocalColors.solar),
              series(batterySpots, GivLocalColors.battery, dashArray: [8, 4]),
              series(gridSpots, GivLocalColors.grid, dashArray: [4, 4]),
              series(consumptionSpots, GivLocalColors.home, dashArray: [2, 2]),
            ],
            lineTouchData: LineTouchData(
              touchTooltipData: LineTouchTooltipData(
                getTooltipColor: (_) => GivLocalColors.background,
                getTooltipItems: (touchedSpots) {
                  return touchedSpots.map((spot) {
                    final idx = spot.spotIndex;
                    final time = timeLabels[idx] ?? '';
                    return LineTooltipItem(
                      '$time  ${spot.y.toStringAsFixed(2)} kW',
                      TextStyle(color: spot.bar.color, fontSize: 11),
                    );
                  }).toList();
                },
              ),
            ),
          ),
        ),
      ),
    );
  }
}
