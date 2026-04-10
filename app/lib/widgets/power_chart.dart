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
        height: 200,
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.bar_chart, size: 40, color: GivLocalColors.textMuted.withAlpha(80)),
              const SizedBox(height: 8),
              const Text('No data for this date', style: TextStyle(color: GivLocalColors.textMuted, fontSize: 14)),
              const SizedBox(height: 4),
              const Text('Try a date when your system was online', style: TextStyle(color: GivLocalColors.textMuted, fontSize: 11)),
            ],
          ),
        ),
      );
    }

    final solarSpots = <FlSpot>[];
    final gridSpots = <FlSpot>[];
    final batterySpots = <FlSpot>[];
    final consumptionSpots = <FlSpot>[];

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
    }

    LineChartBarData _series(
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
          color: color.withOpacity(0.15),
        ),
      );
    }

    return Semantics(
      label: 'Power chart showing solar, battery, grid and consumption over time',
      child: SizedBox(
        height: 200,
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
            titlesData: const FlTitlesData(show: false),
            borderData: FlBorderData(show: false),
            lineBarsData: [
              _series(solarSpots, GivLocalColors.solar),
              _series(batterySpots, GivLocalColors.battery, dashArray: [8, 4]),
              _series(gridSpots, GivLocalColors.grid, dashArray: [4, 4]),
              _series(consumptionSpots, GivLocalColors.home, dashArray: [2, 2]),
            ],
            lineTouchData: LineTouchData(
              touchTooltipData: LineTouchTooltipData(
                getTooltipColor: (_) => GivLocalColors.background,
                getTooltipItems: (touchedSpots) {
                  return touchedSpots.map((spot) {
                    return LineTooltipItem(
                      '${spot.y.toStringAsFixed(2)} kW',
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
