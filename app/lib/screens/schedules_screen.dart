import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/connection_provider.dart';
import '../providers/settings_provider.dart';
import '../theme.dart';
import '../widgets/mode_selector.dart';
import '../widgets/schedule_slot_card.dart';

class SchedulesScreen extends ConsumerStatefulWidget {
  const SchedulesScreen({super.key});

  @override
  ConsumerState<SchedulesScreen> createState() => _SchedulesScreenState();
}

class _SchedulesScreenState extends ConsumerState<SchedulesScreen> {
  // ── Operating mode (0=Eco, 1=Timed, 2=Export) ────────────────────────────
  // Eco mode setting is a boolean: true = eco ON (mode 0), false = timed/export
  // We map: ecoMode true → 0, ecoMode false + discharge enabled → 2 (export),
  // ecoMode false + discharge disabled → 1 (timed)
  int _operatingMode = 1;

  // ── Battery reserve ───────────────────────────────────────────────────────
  double _batteryReserve = 4;

  // ── Charge slot 1 ────────────────────────────────────────────────────────
  String _chargeStart = '00:30';
  String _chargeEnd = '05:00';
  int _chargeTargetSoc = 80;
  bool _chargeEnabled = false;

  // ── Discharge slot 1 ─────────────────────────────────────────────────────
  String _dischargeStart = '16:00';
  String _dischargeEnd = '19:00';
  int _dischargeTargetSoc = 4;
  bool _dischargeEnabled = false;

  bool _loading = true;
  String? _serial;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadSettings());
  }

  Future<void> _loadSettings() async {
    final storage = ref.read(storageServiceProvider);
    final serial = storage.inverterSerial;
    if (serial.isEmpty) {
      setState(() => _loading = false);
      return;
    }
    _serial = serial;

    final api = ref.read(apiServiceProvider);

    // Read all settings concurrently
    final results = await Future.wait([
      api.readSetting(serial, SettingIds.ecoMode),
      api.readSetting(serial, SettingIds.batteryReserve),
      api.readSetting(serial, SettingIds.enableCharge),
      api.readSetting(serial, SettingIds.enableDischarge),
      api.readSetting(serial, SettingIds.chargeSlot1Start),
      api.readSetting(serial, SettingIds.chargeSlot1End),
      api.readSetting(serial, SettingIds.chargeSlot1Soc),
      api.readSetting(serial, SettingIds.dischargeSlot1Start),
      api.readSetting(serial, SettingIds.dischargeSlot1End),
      api.readSetting(serial, SettingIds.dischargeSlot1Soc),
    ]);

    final ecoModeSetting = results[0];
    final batteryReserveSetting = results[1];
    final enableChargeSetting = results[2];
    final enableDischargeSetting = results[3];
    final chargeStartSetting = results[4];
    final chargeEndSetting = results[5];
    final chargeSocSetting = results[6];
    final dischargeStartSetting = results[7];
    final dischargeEndSetting = results[8];
    final dischargeSocSetting = results[9];

    if (!mounted) return;

    setState(() {
      // Eco mode: API returns true/false or 1/0
      final ecoVal = ecoModeSetting?.value;
      final ecoOn = ecoVal == true || ecoVal == 1 || ecoVal == 'true';
      if (ecoOn) {
        _operatingMode = 0;
      } else {
        // distinguish timed vs export by discharge setting
        final dischargeEnabled = enableDischargeSetting?.value;
        final dischargeOn = dischargeEnabled == true ||
            dischargeEnabled == 1 ||
            dischargeEnabled == 'true';
        _operatingMode = dischargeOn ? 2 : 1;
      }

      // Battery reserve
      final reserve = batteryReserveSetting?.value;
      if (reserve != null) {
        _batteryReserve = (reserve is num)
            ? reserve.toDouble().clamp(4.0, 100.0)
            : double.tryParse(reserve.toString())?.clamp(4.0, 100.0) ?? 4.0;
      }

      // Charge slot
      final chargeEnVal = enableChargeSetting?.value;
      _chargeEnabled =
          chargeEnVal == true || chargeEnVal == 1 || chargeEnVal == 'true';

      final chargeStart = chargeStartSetting?.value?.toString();
      if (chargeStart != null && chargeStart.isNotEmpty) {
        _chargeStart = chargeStart;
      }
      final chargeEnd = chargeEndSetting?.value?.toString();
      if (chargeEnd != null && chargeEnd.isNotEmpty) _chargeEnd = chargeEnd;

      final chargeSoc = chargeSocSetting?.value;
      if (chargeSoc != null) {
        _chargeTargetSoc = (chargeSoc is num)
            ? chargeSoc.toInt()
            : int.tryParse(chargeSoc.toString()) ?? 80;
      }

      // Discharge slot
      final dischargeEnVal = enableDischargeSetting?.value;
      _dischargeEnabled = dischargeEnVal == true ||
          dischargeEnVal == 1 ||
          dischargeEnVal == 'true';

      final dischargeStart = dischargeStartSetting?.value?.toString();
      if (dischargeStart != null && dischargeStart.isNotEmpty) {
        _dischargeStart = dischargeStart;
      }
      final dischargeEnd = dischargeEndSetting?.value?.toString();
      if (dischargeEnd != null && dischargeEnd.isNotEmpty) {
        _dischargeEnd = dischargeEnd;
      }

      final dischargeSoc = dischargeSocSetting?.value;
      if (dischargeSoc != null) {
        _dischargeTargetSoc = (dischargeSoc is num)
            ? dischargeSoc.toInt()
            : int.tryParse(dischargeSoc.toString()) ?? 4;
      }

      _loading = false;
    });
  }

  Future<void> _writeSetting(int id, dynamic value) async {
    final serial = _serial;
    if (serial == null || serial.isEmpty) return;
    final api = ref.read(apiServiceProvider);
    await api.writeSetting(serial, id, value);
  }

  void _onModeChanged(int mode) {
    setState(() => _operatingMode = mode);
    // Eco mode is a boolean setting; export mode uses discharge enable
    final ecoOn = mode == 0;
    _writeSetting(SettingIds.ecoMode, ecoOn);
    if (!ecoOn) {
      final dischargeOn = mode == 2;
      _writeSetting(SettingIds.enableDischarge, dischargeOn);
    }
  }

  void _onReserveChanged(double value) {
    setState(() => _batteryReserve = value);
  }

  void _onReserveChangeEnd(double value) {
    _writeSetting(SettingIds.batteryReserve, value.round());
  }

  void _onChargeToggle(bool value) {
    setState(() => _chargeEnabled = value);
    _writeSetting(SettingIds.enableCharge, value);
  }

  void _onDischargeToggle(bool value) {
    setState(() => _dischargeEnabled = value);
    _writeSetting(SettingIds.enableDischarge, value);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Schedules',
          style: TextStyle(
            color: GivLocalColors.textPrimary,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      body: _loading
          ? const Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 12),
                  Text('Loading settings...', style: TextStyle(color: GivLocalColors.textMuted)),
                ],
              ),
            )
          : _serial == null || _serial!.isEmpty
              ? _buildNotConnected()
              : _buildContent(),
    );
  }

  Widget _buildNotConnected() {
    return const Center(
      child: Padding(
        padding: EdgeInsets.all(32),
        child: Text(
          'No inverter connected.\nConfigure your connection in Settings.',
          textAlign: TextAlign.center,
          style: TextStyle(color: GivLocalColors.textSecondary, fontSize: 14),
        ),
      ),
    );
  }

  Widget _buildContent() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Operating Mode
          _SectionHeader(label: 'OPERATING MODE'),
          const SizedBox(height: 8),
          ModeSelector(
            selected: _operatingMode,
            onChanged: _onModeChanged,
          ),
          const SizedBox(height: 24),

          // Battery Reserve
          _SectionHeader(label: 'BATTERY RESERVE'),
          const SizedBox(height: 8),
          _buildReserveCard(),
          const SizedBox(height: 24),

          // Charge Slots
          _SectionHeader(label: 'CHARGE SLOTS'),
          const SizedBox(height: 8),
          ScheduleSlotCard(
            slotNumber: 1,
            startTime: _chargeStart,
            endTime: _chargeEnd,
            targetSoc: _chargeTargetSoc,
            enabled: _chargeEnabled,
            onToggle: _onChargeToggle,
          ),
          const SizedBox(height: 24),

          // Discharge Slots
          _SectionHeader(label: 'DISCHARGE SLOTS'),
          const SizedBox(height: 8),
          ScheduleSlotCard(
            slotNumber: 1,
            startTime: _dischargeStart,
            endTime: _dischargeEnd,
            targetSoc: _dischargeTargetSoc,
            enabled: _dischargeEnabled,
            onToggle: _onDischargeToggle,
          ),
          const SizedBox(height: 32),
        ],
      ),
    );
  }

  Widget _buildReserveCard() {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 10),
      decoration: BoxDecoration(
        color: GivLocalColors.card,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: GivLocalColors.cardBorder),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Minimum charge to keep in battery',
                style: TextStyle(
                  color: GivLocalColors.textSecondary,
                  fontSize: 13,
                ),
              ),
              Text(
                '${_batteryReserve.round()}%',
                style: const TextStyle(
                  color: GivLocalColors.textPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          SliderTheme(
            data: SliderTheme.of(context).copyWith(
              activeTrackColor: GivLocalColors.battery,
              inactiveTrackColor: const Color(0x33FFFFFF),
              thumbColor: GivLocalColors.battery,
              overlayColor: const Color(0x2222C55E),
              trackHeight: 3,
              thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 8),
            ),
            child: Slider(
              value: _batteryReserve,
              min: 4,
              max: 100,
              divisions: 96,
              onChanged: _onReserveChanged,
              onChangeEnd: _onReserveChangeEnd,
            ),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: const [
              Text(
                '4%',
                style: TextStyle(
                  color: GivLocalColors.textMuted,
                  fontSize: 11,
                ),
              ),
              Text(
                '100%',
                style: TextStyle(
                  color: GivLocalColors.textMuted,
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ],
      ),
    );
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
