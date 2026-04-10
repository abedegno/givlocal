import 'dart:ui' show FontFeature;
import 'package:flutter/material.dart';
import '../models/system_data.dart';
import '../theme.dart';
import 'flow_painter.dart';

String _formatPower(int watts) {
  if (watts.abs() >= 1000) {
    return '${(watts / 1000.0).toStringAsFixed(1)} kW';
  }
  return '$watts W';
}

class EnergyFlowDiagram extends StatefulWidget {
  final SystemData data;

  const EnergyFlowDiagram({super.key, required this.data});

  @override
  State<EnergyFlowDiagram> createState() => _EnergyFlowDiagramState();
}

class _EnergyFlowDiagramState extends State<EnergyFlowDiagram>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  bool _animationsEnabled = true;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _animationsEnabled = !MediaQuery.of(context).disableAnimations;
    if (!_animationsEnabled) {
      _controller.stop();
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final data = widget.data;
    // Grid node colour changes based on direction
    // Grid: green + "Export" when exporting, red + "Import" when importing
    final gridColor = data.grid.power < 0 ? GivLocalColors.battery : GivLocalColors.grid;
    final gridLabel = data.grid.power < 0 ? 'Export' : (data.grid.power > 0 ? 'Import' : 'Grid');
    // Battery: show charging/discharging state
    final batteryLabel = data.battery.power > 0 ? 'Charging' : (data.battery.power < 0 ? 'Discharging' : 'Battery');

    return LayoutBuilder(builder: (context, constraints) {
      final w = constraints.maxWidth;
      final h = constraints.maxHeight;

      final solarCenter = Offset(w / 2, 40);
      final homeCenter = Offset(w / 2, h / 2);
      final batteryCenter = Offset(w * 0.15, h / 2);
      final gridCenter = Offset(w * 0.85, h / 2);

      return Semantics(
        label:
            'Energy flow: Solar ${_formatPower(data.solar.power)}, Home ${_formatPower(data.consumption)}, Battery ${data.battery.percent}%, Grid ${_formatPower(data.grid.power)}',
        child: AnimatedBuilder(
          animation: _controller,
          builder: (context, child) {
            return Stack(
              children: [
                CustomPaint(
                  size: Size(w, h),
                  painter: FlowPainter(
                    data: data,
                    solarCenter: solarCenter,
                    homeCenter: homeCenter,
                    batteryCenter: batteryCenter,
                    gridCenter: gridCenter,
                    animationValue: _controller.value,
                    animationsEnabled: _animationsEnabled,
                  ),
                ),
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
                  label: batteryLabel,
                  value: '${data.battery.percent}%',
                ),
                _NodeWidget(
                  center: gridCenter,
                  icon: Icons.electric_bolt,
                  color: gridColor,
                  label: gridLabel,
                  value: _formatPower(data.grid.power.abs()),
                ),
              ],
            );
          },
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
    const nodeRadius = 28.0;
    const totalWidth = 90.0;

    return Positioned(
      left: center.dx - totalWidth / 2,
      top: center.dy - nodeRadius,
      width: totalWidth,
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
                color: color.withAlpha(30),
                border: Border.all(color: color, width: 2),
              ),
              child: Icon(icon, color: color, size: 22),
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
