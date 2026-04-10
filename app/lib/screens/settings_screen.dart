import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/api_service.dart' as api_svc;
import '../theme.dart';
import '../providers/connection_provider.dart';
import '../providers/live_data_provider.dart';
import '../models/device.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  final _localUrlController = TextEditingController();
  final _remoteUrlController = TextEditingController();
  final _apiTokenController = TextEditingController();

  bool _obscureToken = true;
  bool _isTesting = false;
  String? _testResultMessage;
  bool _testResultSuccess = false;

  List<CommunicationDevice> _devices = [];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _loadFromStorage();
    });
  }

  void _loadFromStorage() {
    final storage = ref.read(storageServiceProvider);
    _localUrlController.text = storage.localUrl;
    _remoteUrlController.text = storage.remoteUrl;
    _apiTokenController.text = storage.apiToken;
  }

  @override
  void dispose() {
    _localUrlController.dispose();
    _remoteUrlController.dispose();
    _apiTokenController.dispose();
    super.dispose();
  }

  Future<void> _testConnection() async {
    setState(() {
      _isTesting = true;
      _testResultMessage = null;
    });

    final storage = ref.read(storageServiceProvider);
    storage.localUrl = _localUrlController.text.trim();
    storage.remoteUrl = _remoteUrlController.text.trim();
    storage.apiToken = _apiTokenController.text.trim();

    final api = ref.read(apiServiceProvider);
    await api.connect();

    final newState = api.connectionState;
    ref.read(connectionStateProvider.notifier).state = newState;

    if (newState != api_svc.ConnectionState.disconnected) {
      final devices = await api.getDevices();
      setState(() {
        _devices = devices;
      });

      if (devices.isNotEmpty) {
        final serial = devices.first.inverter.serial;
        if (serial.isNotEmpty) {
          storage.inverterSerial = serial;
          ref.read(liveDataProvider.notifier).startPolling(serial);
        }
      }

      final label =
          newState == api_svc.ConnectionState.local ? 'local' : 'remote';
      setState(() {
        _isTesting = false;
        _testResultSuccess = true;
        _testResultMessage = 'Connected via $label endpoint';
      });
    } else {
      setState(() {
        _isTesting = false;
        _testResultSuccess = false;
        _testResultMessage = 'Connection failed. Check URLs and token.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final connState = ref.watch(connectionStateProvider);
    final isConnected = connState != api_svc.ConnectionState.disconnected;

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Settings',
          style: TextStyle(
            color: GivLocalColors.textPrimary,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _SectionHeader(label: 'CONNECTION'),
            const SizedBox(height: 8),
            _buildConnectionCard(connState, isConnected),
            const SizedBox(height: 24),
            if (isConnected) ...[
              _SectionHeader(label: 'SYSTEM'),
              const SizedBox(height: 8),
              _buildSystemCard(),
              const SizedBox(height: 24),
            ],
            _SectionHeader(label: 'APPEARANCE'),
            const SizedBox(height: 8),
            _buildAppearanceCard(),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildConnectionCard(api_svc.ConnectionState connState, bool isConnected) {
    return Container(
      decoration: BoxDecoration(
        color: GivLocalColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: GivLocalColors.cardBorder),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Status row
          Row(
            children: [
              _statusDot(connState),
              const SizedBox(width: 8),
              Text(
                _statusLabel(connState),
                style: TextStyle(
                  color: _statusColor(connState),
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Local URL
          _FieldLabel(label: 'Local URL'),
          const SizedBox(height: 6),
          _styledTextField(
            controller: _localUrlController,
            hint: 'http://192.168.x.x:8099',
          ),
          const SizedBox(height: 12),

          // Remote URL
          _FieldLabel(label: 'Remote URL'),
          const SizedBox(height: 6),
          _styledTextField(
            controller: _remoteUrlController,
            hint: 'https://givlocal.example.com',
          ),
          const SizedBox(height: 12),

          // API Token
          _FieldLabel(label: 'API Token'),
          const SizedBox(height: 6),
          _styledTextField(
            controller: _apiTokenController,
            hint: 'Bearer token',
            obscure: _obscureToken,
            suffix: IconButton(
              icon: Icon(
                _obscureToken ? Icons.visibility_off : Icons.visibility,
                color: GivLocalColors.textSecondary,
                size: 20,
              ),
              onPressed: () {
                setState(() {
                  _obscureToken = !_obscureToken;
                });
              },
            ),
          ),
          const SizedBox(height: 16),

          // Test Connection button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: GivLocalColors.accent,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              onPressed: _isTesting ? null : _testConnection,
              child: _isTesting
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor:
                            AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Text(
                      'Test Connection',
                      style: TextStyle(
                        fontWeight: FontWeight.w600,
                        fontSize: 15,
                      ),
                    ),
            ),
          ),

          // Test result
          if (_testResultMessage != null) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(
                  _testResultSuccess ? Icons.check_circle : Icons.error,
                  size: 16,
                  color: _testResultSuccess
                      ? GivLocalColors.battery
                      : GivLocalColors.grid,
                ),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    _testResultMessage!,
                    style: TextStyle(
                      color: _testResultSuccess
                          ? GivLocalColors.battery
                          : GivLocalColors.grid,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSystemCard() {
    if (_devices.isEmpty) {
      return Container(
        decoration: BoxDecoration(
          color: GivLocalColors.card,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: GivLocalColors.cardBorder),
        ),
        padding: const EdgeInsets.all(16),
        child: const Text(
          'No device info available.',
          style: TextStyle(color: GivLocalColors.textSecondary, fontSize: 13),
        ),
      );
    }

    final device = _devices.first;
    final inverter = device.inverter;

    return Container(
      decoration: BoxDecoration(
        color: GivLocalColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: GivLocalColors.cardBorder),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          _InfoRow(label: 'Inverter Serial', value: inverter.serial),
          _InfoRow(
              label: 'Model', value: inverter.model ?? 'Unknown'),
          _InfoRow(
              label: 'Firmware',
              value: inverter.firmwareVersion ?? 'Unknown'),
          _InfoRow(label: 'Status', value: inverter.status),
        ],
      ),
    );
  }

  Widget _buildAppearanceCard() {
    return Container(
      decoration: BoxDecoration(
        color: GivLocalColors.card,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: GivLocalColors.cardBorder),
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Theme',
            style: TextStyle(
              color: GivLocalColors.textSecondary,
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              _ThemeChip(label: 'System', selected: false),
              const SizedBox(width: 8),
              _ThemeChip(label: 'Dark', selected: true),
              const SizedBox(width: 8),
              _ThemeChip(label: 'Light', selected: false),
            ],
          ),
        ],
      ),
    );
  }

  Widget _styledTextField({
    required TextEditingController controller,
    required String hint,
    bool obscure = false,
    Widget? suffix,
  }) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      style: const TextStyle(
        color: GivLocalColors.textPrimary,
        fontSize: 14,
      ),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(
          color: GivLocalColors.textMuted,
          fontSize: 14,
        ),
        suffixIcon: suffix,
        filled: true,
        fillColor: const Color(0x14FFFFFF),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: GivLocalColors.cardBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: GivLocalColors.cardBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide:
              const BorderSide(color: GivLocalColors.accent, width: 1.5),
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      ),
    );
  }

  Widget _statusDot(api_svc.ConnectionState state) {
    return Container(
      width: 10,
      height: 10,
      decoration: BoxDecoration(
        color: _statusColor(state),
        shape: BoxShape.circle,
      ),
    );
  }

  Color _statusColor(api_svc.ConnectionState state) {
    switch (state) {
      case api_svc.ConnectionState.local:
        return GivLocalColors.battery;
      case api_svc.ConnectionState.remote:
        return Colors.blueAccent;
      case api_svc.ConnectionState.disconnected:
        return GivLocalColors.grid;
    }
  }

  String _statusLabel(api_svc.ConnectionState state) {
    switch (state) {
      case api_svc.ConnectionState.local:
        return 'Connected (Local)';
      case api_svc.ConnectionState.remote:
        return 'Connected (Remote)';
      case api_svc.ConnectionState.disconnected:
        return 'Disconnected';
    }
  }
}

class _SectionHeader extends StatelessWidget {
  final String label;
  const _SectionHeader({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: const TextStyle(
        color: GivLocalColors.textMuted,
        fontSize: 11,
        fontWeight: FontWeight.w600,
        letterSpacing: 1.2,
      ),
    );
  }
}

class _FieldLabel extends StatelessWidget {
  final String label;
  const _FieldLabel({required this.label});

  @override
  Widget build(BuildContext context) {
    return Text(
      label,
      style: const TextStyle(
        color: GivLocalColors.textSecondary,
        fontSize: 13,
        fontWeight: FontWeight.w500,
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  final String label;
  final String value;
  const _InfoRow({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              label,
              style: const TextStyle(
                color: GivLocalColors.textSecondary,
                fontSize: 13,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: GivLocalColors.textPrimary,
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ThemeChip extends StatelessWidget {
  final String label;
  final bool selected;
  const _ThemeChip({required this.label, required this.selected});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
      decoration: BoxDecoration(
        color: selected ? GivLocalColors.accent : Colors.transparent,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color:
              selected ? GivLocalColors.accent : GivLocalColors.cardBorder,
        ),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: selected
              ? Colors.white
              : GivLocalColors.textSecondary,
          fontSize: 13,
          fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
        ),
      ),
    );
  }
}
