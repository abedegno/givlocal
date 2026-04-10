import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'connection_provider.dart';

final selectedDateProvider = StateProvider<DateTime>((ref) => DateTime.now());

final dataPointsProvider = FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final date = ref.watch(selectedDateProvider);
  final api = ref.read(apiServiceProvider);
  final storage = ref.read(storageServiceProvider);
  final dateStr = DateFormat('yyyy-MM-dd').format(date);
  return api.getDataPoints(storage.inverterSerial, dateStr);
});
