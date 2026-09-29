import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../theme/app_theme.dart';

class AiAssistantScreen extends StatefulWidget {
  const AiAssistantScreen({super.key});

  @override
  State<AiAssistantScreen> createState() => _AiAssistantScreenState();
}

class _ChatMessage {
  final String role; // "user" | "assistant"
  final String content;
  final Map<String, dynamic>? sensorSnapshot;
  final DateTime timestamp;

  _ChatMessage({
    required this.role,
    required this.content,
    this.sensorSnapshot,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}

class _AiAssistantScreenState extends State<AiAssistantScreen> {
  final TextEditingController _inputCtrl = TextEditingController();
  final ScrollController _scrollCtrl = ScrollController();
  final List<_ChatMessage> _messages = [];
  bool _loading = false;
  bool? _aiOnline;

  static const _suggestions = [
    'How are the plants doing?',
    'Is the temperature safe?',
    'Should I water the plants?',
    'Give me a full farm status',
    'Explain current light conditions',
    'What actions should I take?',
  ];

  @override
  void initState() {
    super.initState();
    _checkAiStatus();
  }

  @override
  void dispose() {
    _inputCtrl.dispose();
    _scrollCtrl.dispose();
    super.dispose();
  }

  Future<void> _checkAiStatus() async {
    try {
      final res = await http
          .get(Uri.parse('${AppConfig.baseUrl}/api/v1/ai/status'))
          .timeout(const Duration(seconds: 5));
      if (!mounted) return;
      if (res.statusCode == 200) {
        final data = json.decode(res.body);
        setState(
          () => _aiOnline =
              data['ollama_reachable'] == true &&
              data['model_available'] == true,
        );
      }
    } catch (_) {
      if (!mounted) return;
      setState(() => _aiOnline = false);
    }
  }

  Future<void> _sendMessage([String? text]) async {
    final msg = (text ?? _inputCtrl.text).trim();
    if (msg.isEmpty || _loading) return;

    _inputCtrl.clear();
    setState(() {
      _messages.add(_ChatMessage(role: 'user', content: msg));
      _loading = true;
    });
    _scrollToBottom();

    try {
      final res = await http
          .post(
            Uri.parse('${AppConfig.baseUrl}/api/v1/ai/chat'),
            headers: {'Content-Type': 'application/json'},
            body: json.encode({
              'message': msg,
              'include_sensor_data': true,
              'farm_id': 'farm_001',
            }),
          )
          .timeout(const Duration(seconds: 120));

      if (res.statusCode != 200) {
        final err = json.decode(res.body);
        throw Exception(err['detail'] ?? 'HTTP ${res.statusCode}');
      }

      final data = json.decode(res.body);
      setState(() {
        _messages.add(
          _ChatMessage(
            role: 'assistant',
            content: data['reply'] ?? '',
            sensorSnapshot: data['sensor_snapshot'] as Map<String, dynamic>?,
          ),
        );
      });
    } catch (e) {
      setState(() {
        _messages.add(_ChatMessage(role: 'assistant', content: '⚠️ Error: $e'));
      });
    } finally {
      setState(() => _loading = false);
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent + 80,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF0F1219) : Colors.grey.shade50,
      appBar: AppBar(
        backgroundColor: isDark ? const Color(0xFF161B26) : Colors.white,
        surfaceTintColor: Colors.transparent,
        title: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(10),
                gradient: const LinearGradient(
                  colors: [Color(0xFF8B5CF6), Color(0xFFD946EF)],
                ),
              ),
              child: const Icon(
                Icons.auto_awesome,
                size: 16,
                color: Colors.white,
              ),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Farm AI',
                  style: GoogleFonts.inter(
                    fontSize: 15,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                Text(
                  'LLaMA 3 · ${_aiOnline == null
                      ? 'checking…'
                      : _aiOnline!
                      ? 'online'
                      : 'offline'}',
                  style: GoogleFonts.robotoMono(
                    fontSize: 10,
                    color: isDark ? Colors.white38 : Colors.black38,
                  ),
                ),
              ],
            ),
            const Spacer(),
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: _aiOnline == null
                    ? Colors.amber
                    : _aiOnline!
                    ? AppColors.emerald500
                    : Colors.red,
              ),
            ),
          ],
        ),
      ),
      body: Column(
        children: [
          // Messages
          Expanded(
            child: _messages.isEmpty ? _buildEmptyState() : _buildChat(isDark),
          ),
          // Input
          _buildInput(isDark),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 64,
              height: 64,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                gradient: LinearGradient(
                  colors: [
                    const Color(0xFF8B5CF6).withValues(alpha: 0.2),
                    const Color(0xFFD946EF).withValues(alpha: 0.2),
                  ],
                ),
                border: Border.all(
                  color: const Color(0xFF8B5CF6).withValues(alpha: 0.2),
                ),
              ),
              child: const Icon(
                Icons.smart_toy_outlined,
                size: 30,
                color: Color(0xFF8B5CF6),
              ),
            ),
            const SizedBox(height: 20),
            Text(
              'Farm AI Assistant',
              style: GoogleFonts.inter(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: isDark ? Colors.white70 : Colors.black87,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Ask about your plants, sensor readings,\nor get growing recommendations.',
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(
                fontSize: 13,
                color: isDark ? Colors.white30 : Colors.black38,
                height: 1.5,
              ),
            ),
            const SizedBox(height: 24),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: _suggestions
                  .map(
                    (s) =>
                        _SuggestionChip(label: s, onTap: () => _sendMessage(s)),
                  )
                  .toList(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChat(bool isDark) {
    return ListView.builder(
      controller: _scrollCtrl,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      itemCount: _messages.length + (_loading ? 1 : 0),
      itemBuilder: (ctx, i) {
        if (i == _messages.length) {
          // Loading indicator
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _botAvatar(),
                const SizedBox(width: 10),
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: isDark
                        ? Colors.white.withValues(alpha: 0.05)
                        : Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: isDark ? Colors.white10 : Colors.black12,
                    ),
                  ),
                  child: const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Color(0xFF8B5CF6),
                    ),
                  ),
                ),
              ],
            ),
          );
        }

        final msg = _messages[i];
        return _MessageBubble(
          msg: msg,
          isDark: isDark,
          botAvatar: _botAvatar(),
        );
      },
    );
  }

  Widget _botAvatar() {
    return Container(
      width: 28,
      height: 28,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        color: const Color(0xFF8B5CF6).withValues(alpha: 0.2),
      ),
      child: const Icon(
        Icons.smart_toy_outlined,
        size: 14,
        color: Color(0xFF8B5CF6),
      ),
    );
  }

  Widget _buildInput(bool isDark) {
    return Container(
      padding: EdgeInsets.fromLTRB(
        16,
        12,
        16,
        MediaQuery.of(context).padding.bottom + 12,
      ),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF161B26) : Colors.white,
        border: Border(
          top: BorderSide(
            color: isDark
                ? Colors.white10
                : Colors.black.withValues(alpha: 0.06),
          ),
        ),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _inputCtrl,
              enabled: !_loading,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _sendMessage(),
              style: GoogleFonts.inter(fontSize: 14),
              decoration: InputDecoration(
                hintText: 'Ask about your farm…',
                hintStyle: GoogleFonts.inter(
                  fontSize: 14,
                  color: isDark ? Colors.white24 : Colors.black26,
                ),
                filled: true,
                fillColor: isDark
                    ? Colors.white.withValues(alpha: 0.05)
                    : Colors.grey.shade100,
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(14),
                  borderSide: BorderSide.none,
                ),
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          GestureDetector(
            onTap: _loading ? null : () => _sendMessage(),
            child: Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(14),
                color: const Color(0xFF8B5CF6),
              ),
              child: _loading
                  ? const Padding(
                      padding: EdgeInsets.all(12),
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(
                      Icons.send_rounded,
                      size: 20,
                      color: Colors.white,
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

// ── Suggestion chip ─────────────────────────────────────────────────────────

class _SuggestionChip extends StatelessWidget {
  final String label;
  final VoidCallback onTap;

  const _SuggestionChip({required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: isDark ? Colors.white12 : Colors.black12),
          color: isDark ? Colors.white.withValues(alpha: 0.04) : Colors.white,
        ),
        child: Text(
          label,
          style: GoogleFonts.inter(
            fontSize: 12,
            color: isDark ? Colors.white54 : Colors.black54,
          ),
        ),
      ),
    );
  }
}

// ── Message bubble ──────────────────────────────────────────────────────────

class _MessageBubble extends StatelessWidget {
  final _ChatMessage msg;
  final bool isDark;
  final Widget botAvatar;

  const _MessageBubble({
    required this.msg,
    required this.isDark,
    required this.botAvatar,
  });

  @override
  Widget build(BuildContext context) {
    final isUser = msg.role == 'user';

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: isUser
            ? MainAxisAlignment.end
            : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[botAvatar, const SizedBox(width: 10)],
          Flexible(
            child: Column(
              crossAxisAlignment: isUser
                  ? CrossAxisAlignment.end
                  : CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 14,
                    vertical: 10,
                  ),
                  decoration: BoxDecoration(
                    color: isUser
                        ? const Color(0xFF8B5CF6)
                        : isDark
                        ? Colors.white.withValues(alpha: 0.05)
                        : Colors.white,
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(16),
                      topRight: const Radius.circular(16),
                      bottomLeft: Radius.circular(isUser ? 16 : 4),
                      bottomRight: Radius.circular(isUser ? 4 : 16),
                    ),
                    border: isUser
                        ? null
                        : Border.all(
                            color: isDark ? Colors.white10 : Colors.black12,
                          ),
                  ),
                  child: Text(
                    msg.content,
                    style: GoogleFonts.inter(
                      fontSize: 13,
                      height: 1.5,
                      color: isUser
                          ? Colors.white
                          : isDark
                          ? Colors.white70
                          : Colors.black87,
                    ),
                  ),
                ),

                // Sensor snapshot badges
                if (msg.sensorSnapshot != null) ...[
                  const SizedBox(height: 6),
                  Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    children: [
                      if (msg.sensorSnapshot!['temperature'] != null)
                        _sensorBadge(
                          Icons.thermostat,
                          '${msg.sensorSnapshot!['temperature']}°C',
                          Colors.orange,
                        ),
                      if (msg.sensorSnapshot!['humidity'] != null)
                        _sensorBadge(
                          Icons.water_drop,
                          '${msg.sensorSnapshot!['humidity']}%',
                          Colors.cyan,
                        ),
                      if (msg.sensorSnapshot!['light_level'] != null)
                        _sensorBadge(
                          Icons.light_mode,
                          '${msg.sensorSnapshot!['light_level']}%',
                          Colors.amber,
                        ),
                      if (msg.sensorSnapshot!['soil_moisture'] != null)
                        _sensorBadge(
                          Icons.grass,
                          '${msg.sensorSnapshot!['soil_moisture']}%',
                          AppColors.emerald500,
                        ),
                    ],
                  ),
                ],

                const SizedBox(height: 4),
                Text(
                  '${msg.timestamp.hour.toString().padLeft(2, '0')}:${msg.timestamp.minute.toString().padLeft(2, '0')}',
                  style: GoogleFonts.robotoMono(
                    fontSize: 9,
                    color: isDark ? Colors.white12 : Colors.black12,
                  ),
                ),
              ],
            ),
          ),
          if (isUser) ...[
            const SizedBox(width: 10),
            Container(
              width: 28,
              height: 28,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(8),
                color: isDark
                    ? Colors.white.withValues(alpha: 0.1)
                    : Colors.black.withValues(alpha: 0.06),
              ),
              child: Icon(
                Icons.person,
                size: 14,
                color: isDark ? Colors.white54 : Colors.black45,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _sensorBadge(IconData icon, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(6),
        color: color.withValues(alpha: 0.1),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 10, color: color),
          const SizedBox(width: 3),
          Text(
            value,
            style: GoogleFonts.robotoMono(
              fontSize: 10,
              fontWeight: FontWeight.w600,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
