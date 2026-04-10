import 'package:flutter/material.dart';
import 'dart:ui' show FontFeature;
import '../models/system_data.dart';
import '../theme.dart';
import 'flow_painter.dart';

String _formatPower(int watts) {
  if (watts.abs() >= 1000) {
    return '${(watts / 1000.0).toStringAsFixed(1)} kW';
  }
  return '$watts W';
}

class EnergyFlowDiagram extends StatelessWidget {
  final SystemData data;

  const EnergyFlowDiagram({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      final w = constraints.maxWidth;
      final h = constraints.maxHeight;

      // Diamond layout: solar top, home center, battery left, grid right
      final solarCenter = Offset(w / 2, 40);
      final homeCenter = Offset(w / 2, h / 2);
      final batteryCenter = Offset(w * 0.15, h / 2);
      final gridCenter = Offset(w * 0.85, h / 2);

      return Semantics(
        label: 'Energy flow: Solar ${_formatPower(data.solar.power)}, Home ${_formatPower(data.consumption)}, Battery ${data.battery.percent}%, Grid ${_formatPower(data.grid.power)}',
        child: Stack(
          children: [
            // Flow lines layer
            CustomPaint(
              size: Size(w, h),
              painter: FlowPainter(
                data: data,
                solarCenter: solarCenter,
                homeCenter: homeCenter,
                batteryCenter: batteryCenter,
                gridCenter: gridCenter,
              ),
            ),
            // Nodes
            _NodeWidget(
              center: solarCenter,
              icon: Icons.wb_sunny,
              color: GivLocalColors.solar,
              label: 'Solar',
              value: _formatPower(data.solar.power),
            ),
            _NodeWidget(
              center: homeCenter,
              icon: Icons.home,
              color: GivLocalColors.home,
              label: 'Home',
              value: _formatPower(data.consumption),
            ),
            _NodeWidget(
              center: batteryCenter,
              icon: Icons.battery_charging_full,
              color: GivLocalColors.battery,
              label: 'Battery',
              value: '${data.battery.percent}%',
            ),
            _NodeWidget(
              center: gridCenter,
              icon: Icons.electric_bolt,
              color: GivLocalColors.grid,
              label: 'Grid',
              value: _formatPower(data.grid.power.abs()),
            ),
          ],
        ),
      );
    });
  }
}

class _NodeWidget extends StatelessWidget {
  final Offset center;
  final IconData icon;
  final Color color;
  final String label;
  final String value;

  const _NodeWidget({
    required this.center,
    required this.icon,
    required this.color,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    const nodeRadius = 32.0;
    const totalHeight = nodeRadius * 2 + 36; // circle + label + value
    const totalWidth = 90.0;

    return Positioned(
      left: center.dx - totalWidth / 2,
      top: center.dy - nodeRadius,
      width: totalWidth,
      height: totalHeight,
      child: Semantics(
        label: '$label: $value',
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: nodeRadius * 2,
              height: nodeRadius * 2,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: color.withValues(alpha: 0.15),
                border: Border.all(color: color, width: 2),
              ),
              child: Icon(icon, color: color, size: 24),
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: const TextStyle(
                color: GivLocalColors.textSecondary,
                fontSize: 12,
              ),
            ),
            Text(
              value,
              style: const TextStyle(
                color: GivLocalColors.textPrimary,
                fontSize: 16,
                fontWeight: FontWeight.w600,
                fontFeatures: [FontFeature.tabularFigures()],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
