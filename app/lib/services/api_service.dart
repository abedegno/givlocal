import 'package:dio/dio.dart';

import '../models/system_data.dart';
import '../models/meter_data.dart';
import '../models/setting.dart';
import '../models/device.dart';
import 'storage_service.dart';

enum ConnectionState { local, remote, disconnected }

class ApiService {
  final StorageService _storage;
  final Dio _dio;

  ConnectionState connectionState = ConnectionState.disconnected;
  String _baseUrl = '';

  ApiService(this._storage) : _dio = Dio();

  Map<String, String> get _headers => {
        'Authorization': 'Bearer ${_storage.apiToken}',
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      };

  Future<void> connect() async {
    final localUrl = _storage.localUrl;
    final remoteUrl = _storage.remoteUrl;

    // Try local URL first with 2s timeout
    if (localUrl.isNotEmpty) {
      try {
        final response = await _dio.get(
          '$localUrl/v1/communication-device',
          options: Options(
            headers: _headers,
            receiveTimeout: const Duration(seconds: 2),
            sendTimeout: const Duration(seconds: 2),
          ),
        );
        if (response.statusCode != null && response.statusCode! < 400) {
          _baseUrl = localUrl;
          connectionState = ConnectionState.local;
          return;
        }
      } catch (_) {
        // Fall through to remote
      }
    }

    // Try remote URL with 5s timeout
    if (remoteUrl.isNotEmpty) {
      try {
        final response = await _dio.get(
          '$remoteUrl/v1/communication-device',
          options: Options(
            headers: _headers,
            receiveTimeout: const Duration(seconds: 5),
            sendTimeout: const Duration(seconds: 5),
          ),
        );
        if (response.statusCode != null && response.statusCode! < 400) {
          _baseUrl = remoteUrl;
          connectionState = ConnectionState.remote;
          return;
        }
      } catch (_) {
        // Fall through to disconnected
      }
    }

    connectionState = ConnectionState.disconnected;
  }

  Future<T?> _get<T>(
    String path,
    T Function(Map<String, dynamic>) fromJson,
  ) async {
    if (connectionState == ConnectionState.disconnected) return null;
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '$_baseUrl$path',
        options: Options(headers: _headers),
      );
      final data = response.data;
      if (data == null) return null;
      return fromJson(data);
    } catch (_) {
      return null;
    }
  }

  Future<SystemData?> getSystemData(String serial) {
    return _get(
      '/v1/inverter/$serial/system-data-latest',
      (json) => SystemData.fromJson(json['data'] as Map<String, dynamic>? ?? json),
    );
  }

  Future<MeterData?> getMeterData(String serial) {
    return _get(
      '/v1/inverter/$serial/meter-data-latest',
      (json) => MeterData.fromJson(json['data'] as Map<String, dynamic>? ?? json),
    );
  }

  Future<List<CommunicationDevice>> getDevices() async {
    if (connectionState == ConnectionState.disconnected) return [];
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '$_baseUrl/v1/communication-device',
        options: Options(headers: _headers),
      );
      final data = response.data;
      if (data == null) return [];
      final list = data['data'] as List<dynamic>? ?? [];
      return list
          .map((e) => CommunicationDevice.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<List<InverterSetting>> getSettings(String serial) async {
    if (connectionState == ConnectionState.disconnected) return [];
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '$_baseUrl/v1/inverter/$serial/settings',
        options: Options(headers: _headers),
      );
      final data = response.data;
      if (data == null) return [];
      final list = data['data'] as List<dynamic>? ?? [];
      return list
          .map((e) => InverterSetting.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<InverterSetting?> readSetting(String serial, int id) async {
    if (connectionState == ConnectionState.disconnected) return null;
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '$_baseUrl/v1/inverter/$serial/settings/$id/read',
        options: Options(headers: _headers),
      );
      final data = response.data;
      if (data == null) return null;
      final inner = data['data'] as Map<String, dynamic>? ?? data;
      return InverterSetting(id: id, name: '', validation: '', value: inner['value']);
    } catch (_) {
      return null;
    }
  }

  Future<InverterSetting?> writeSetting(
      String serial, int id, dynamic value) async {
    if (connectionState == ConnectionState.disconnected) return null;
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '$_baseUrl/v1/inverter/$serial/settings/$id/write',
        data: {'value': value},
        options: Options(headers: _headers),
      );
      final data = response.data;
      if (data == null) return null;
      return InverterSetting.fromJson(
          data['data'] as Map<String, dynamic>? ?? data);
    } catch (_) {
      return null;
    }
  }

  Future<List<Map<String, dynamic>>> getDataPoints(
      String serial, String date) async {
    if (connectionState == ConnectionState.disconnected) return [];
    try {
      final response = await _dio.get<Map<String, dynamic>>(
        '$_baseUrl/v1/inverter/$serial/data-points/$date?pageSize=2000',
        options: Options(headers: _headers),
      );
      final data = response.data;
      if (data == null) return [];
      final list = data['data'] as List<dynamic>? ?? [];
      return list.cast<Map<String, dynamic>>();
    } catch (_) {
      return [];
    }
  }
}
