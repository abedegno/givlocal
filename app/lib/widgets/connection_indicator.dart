import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/api_service.dart' as api_svc;
import '../providers/connection_provider.dart';
import '../theme.dart';

class ConnectionIndicator extends ConsumerWidget {
  const ConnectionIndicator({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(connectionStateProvider);

    final Color dotColor;
    final String label;

    switch (state) {
      case api_svc.ConnectionState.local:
        dotColor = GivLocalColors.battery; // green
        label = 'Local';
      case api_svc.ConnectionState.remote:
        dotColor = Colors.blue;
        label = 'Remote';
      case api_svc.ConnectionState.disconnected:
        dotColor = GivLocalColors.grid; // red
        label = 'Disconnected';
    }

    return Semantics(
      label: 'Connection status: $label',
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: dotColor,
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: const TextStyle(
              color: GivLocalColors.textSecondary,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}
