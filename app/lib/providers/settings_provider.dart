import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/setting.dart';
import 'connection_provider.dart';

class SettingIds {
  static const ecoMode = 24;
  static const batteryReserve = 71;
  static const enableCharge = 66;
  static const enableDischarge = 56;
  static const chargeSlot1Start = 64;
  static const chargeSlot1End = 65;
  static const chargeSlot1Soc = 101;
  static const dischargeSlot1Start = 53;
  static const dischargeSlot1End = 54;
  static const dischargeSlot1Soc = 129;
}

/// Fetches all settings for a given serial number.
final settingsListProvider =
    FutureProvider.family<List<InverterSetting>, String>((ref, serial) async {
  final api = ref.read(apiServiceProvider);
  return api.getSettings(serial);
});

/// Fetches a single setting value for (serial, settingId).
final settingValueProvider =
    FutureProvider.family<InverterSetting?, (String, int)>((ref, args) async {
  final serial = args.$1;
  final id = args.$2;
  final api = ref.read(apiServiceProvider);
  return api.readSetting(serial, id);
});
