/// Simple shared configuration for the app backend URL.
///
/// [_host] points to the **cloud backend on the laptop** (port 8000).
/// Update this with your laptop's current IP address before running the app,
/// or use the Settings screen at runtime to change it without recompiling.
class AppConfig {
  // Cloud backend URL — update with your laptop's IP or hostname.
  // The cloud backend runs on the laptop via:  docker-compose up
  // Example:  '192.168.1.42:8000'
  static String _host = '192.168.1.4:8000'; // Laptop IP on home Wi-Fi

  /// Relay-capable backend (port 8001) — has working MQTT connection.
  static String _relayHost = '192.168.1.4:8001';

  static String get host => _host;
  static set host(String value) => _host = value;

  static String get baseUrl => 'http://$_host';
  static String get relayBaseUrl => 'http://$_relayHost';
  static String get wsUrl => 'ws://$_host/ws/farm_001';
}
