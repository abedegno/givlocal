import 'dart:math';
import 'package:flutter/material.dart';
import '../models/system_data.dart';
import '../theme.dart';

class FlowPainter extends CustomPainter {
  final SystemData data;
  final Offset solarCenter;
  final Offset homeCenter;
  final Offset batteryCenter;
  final Offset gridCenter;
  final double animationValue; // 0.0 to 1.0, drives photon positions
  final bool animationsEnabled;

  FlowPainter({
    required this.data,
    required this.solarCenter,
    required this.homeCenter,
    required this.batteryCenter,
    required this.gridCenter,
    this.animationValue = 0.0,
    this.animationsEnabled = true,
  });

  static const _nodeRadius = 28.0;
  static const _margin = _nodeRadius + 8;

  double _clampWidth(int power) {
    final abs = power.abs().toDouble();
    return (abs / 1000.0 * 4.0).clamp(1.5, 4.0);
  }

  Offset _shorten(Offset from, Offset to, double margin) {
    final dir = to - from;
    final len = dir.distance;
    if (len <= margin) return from;
    return to - dir / len * margin;
  }

  void _drawFlow(
    Canvas canvas,
    Offset rawFrom,
    Offset rawTo,
    Color color,
    int power,
  ) {
    final from = _shorten(rawTo, rawFrom, _margin);
    final to = _shorten(rawFrom, rawTo, _margin);
    final width = _clampWidth(power);

    // Draw the line
    final linePaint = Paint()
      ..color = color.withAlpha(80)
      ..strokeWidth = width
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(from, to, linePaint);

    // Draw arrowhead
    final direction = to - from;
    final length = direction.distance;
    if (length == 0) return;
    final unit = direction / length;
    final arrowSize = width * 3.0;
    final arrowBase = to - unit * arrowSize;
    final perp = Offset(-unit.dy, unit.dx);
    final arrowPath = Path()
      ..moveTo(to.dx, to.dy)
      ..lineTo(arrowBase.dx + perp.dx * arrowSize * 0.5,
          arrowBase.dy + perp.dy * arrowSize * 0.5)
      ..lineTo(arrowBase.dx - perp.dx * arrowSize * 0.5,
          arrowBase.dy - perp.dy * arrowSize * 0.5)
      ..close();
    canvas.drawPath(
      arrowPath,
      Paint()
        ..color = color.withAlpha(120)
        ..style = PaintingStyle.fill,
    );

    // Draw animated photons
    if (animationsEnabled && power.abs() > 0) {
      // Number of photons based on power magnitude
      final numPhotons = min(4, max(1, power.abs() ~/ 500));
      final photonRadius = width * 0.8;
      final photonPaint = Paint()
        ..color = color
        ..style = PaintingStyle.fill;
      final glowPaint = Paint()
        ..color = color.withAlpha(60)
        ..style = PaintingStyle.fill;

      for (int i = 0; i < numPhotons; i++) {
        // Stagger photons evenly along the line, offset by animation
        final t = ((animationValue + i / numPhotons) % 1.0);
        final pos = Offset.lerp(from, to, t)!;
        // Glow
        canvas.drawCircle(pos, photonRadius * 2.5, glowPaint);
        // Core
        canvas.drawCircle(pos, photonRadius, photonPaint);
      }
    }
  }

  @override
  void paint(Canvas canvas, Size size) {
    // Solar -> Home
    if (data.solar.power > 0) {
      _drawFlow(canvas, solarCenter, homeCenter, GivLocalColors.solar, data.solar.power);
    }

    // Battery <-> Home
    if (data.battery.power != 0) {
      final charging = data.battery.power > 0;
      _drawFlow(
        canvas,
        charging ? homeCenter : batteryCenter,
        charging ? batteryCenter : homeCenter,
        GivLocalColors.battery,
        data.battery.power.abs(),
      );
    }

    // Grid <-> Home (green for export, red for import)
    if (data.grid.power != 0) {
      final importing = data.grid.power > 0;
      final color = importing ? GivLocalColors.grid : GivLocalColors.battery;
      _drawFlow(
        canvas,
        importing ? gridCenter : homeCenter,
        importing ? homeCenter : gridCenter,
        color,
        data.grid.power.abs(),
      );
    }
  }

  @override
  bool shouldRepaint(FlowPainter oldDelegate) {
    return oldDelegate.data != data || oldDelegate.animationValue != animationValue;
  }
}
