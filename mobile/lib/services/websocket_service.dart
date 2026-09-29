/// WebSocket service for real-time sensor data from FastAPI backend.

import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../models/sensor_data.dart';

class WebSocketService {
  final String url;
  WebSocketChannel? _channel;
  Timer? _reconnectTimer;
  bool _disposed = false;

  final _controller = StreamController<SensorData>.broadcast();
  final _connectionController = StreamController<bool>.broadcast();

  Stream<SensorData> get sensorStream => _controller.stream;
  Stream<bool> get connectionStream => _connectionController.stream;
  bool _isConnected = false;
  bool get isConnected => _isConnected;

  WebSocketService({required this.url});

  void connect() {
    if (_disposed) return;
    try {
      _channel = WebSocketChannel.connect(Uri.parse(url));
      _isConnected = true;
      _connectionController.add(true);

      _channel!.stream.listen(
        (message) {
          try {
            final data = json.decode(message);
            if (data['type'] == 'sensor_update' && data['data'] != null) {
              _controller.add(SensorData.fromJson(data['data']));
            }
          } catch (_) {}
        },
        onError: (_) => _handleDisconnect(),
        onDone: () => _handleDisconnect(),
      );
    } catch (_) {
      _handleDisconnect();
    }
  }

  void _handleDisconnect() {
    _isConnected = false;
    _connectionController.add(false);
    _channel = null;
    if (!_disposed) {
      _reconnectTimer?.cancel();
      _reconnectTimer = Timer(const Duration(seconds: 3), connect);
    }
  }

  void dispose() {
    _disposed = true;
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _controller.close();
    _connectionController.close();
  }
}
