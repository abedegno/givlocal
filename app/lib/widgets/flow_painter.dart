import 'package:flutter/material.dart';
import '../models/system_data.dart';
import '../theme.dart';

// TODO: When adding flow animations, check MediaQuery.disableAnimations
// to respect prefers-reduced-motion. Keep durations 150-300ms.
class FlowPainter extends CustomPainter {
  final SystemData data;
  final Offset solarCenter;
  final Offset homeCenter;
  final Offset batteryCenter;
  final Offset gridCenter;

  FlowPainter({
    required this.data,
    required this.solarCenter,
    required this.homeCenter,
    required this.batteryCenter,
    required this.gridCenter,
  });

  double _clampWidth(int power) {
    final abs = power.abs().toDouble();
    return (abs / 1000.0 * 4.0).clamp(1.5, 4.0);
  }

  void _drawArrow(Canvas canvas, Offset from, Offset to, Color color, double width) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = width
      ..style = PaintingStyle.stroke
      ..strokeCap = StrokeCap.round;

    canvas.drawLine(from, to, paint);

    // Draw arrowhead
    final direction = (to - from);
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
        ..color = color
        ..style = PaintingStyle.fill,
    );
  }

  @override
  void paint(Canvas canvas, Size size) {
    const nodeRadius = 32.0;

    // Helper: shorten line so arrow sits outside node circles
    Offset shorten(Offset from, Offset to, double margin) {
      final dir = to - from;
      final len = dir.distance;
      if (len <= margin) return from;
      return to - dir / len * margin;
    }

    // Solar -> Home (if solar power > 0)
    if (data.solar.power > 0) {
      final end = shorten(solarCenter, homeCenter, nodeRadius + 8);
      final start = shorten(homeCenter, solarCenter, nodeRadius + 8);
      _drawArrow(canvas, start, end, GivLocalColors.solar,
          _clampWidth(data.solar.power));
    }

    // Battery <-> Home
    if (data.battery.power != 0) {
      final charging = data.battery.power > 0; // positive = charging
      final from = charging ? homeCenter : batteryCenter;
      final to = charging ? batteryCenter : homeCenter;
      final endPoint = shorten(from, to, nodeRadius + 8);
      final startPoint = shorten(to, from, nodeRadius + 8);
      _drawArrow(canvas, startPoint, endPoint, GivLocalColors.battery,
          _clampWidth(data.battery.power));
    }

    // Grid <-> Home
    if (data.grid.power != 0) {
      final importing = data.grid.power > 0; // positive = importing from grid
      final from = importing ? gridCenter : homeCenter;
      final to = importing ? homeCenter : gridCenter;
      final endPoint = shorten(from, to, nodeRadius + 8);
      final startPoint = shorten(to, from, nodeRadius + 8);
      _drawArrow(canvas, startPoint, endPoint, GivLocalColors.grid,
          _clampWidth(data.grid.power));
    }
  }

  @override
  bool shouldRepaint(FlowPainter oldDelegate) {
    return oldDelegate.data != data;
  }
}
