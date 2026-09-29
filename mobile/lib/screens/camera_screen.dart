import 'dart:async';
import 'dart:convert';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../config/app_config.dart';
import '../theme/app_theme.dart';

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key});

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  // ── State ────────────────────────────────────────────────────────────────
  Map<String, dynamic>? _latest;
  List<Map<String, dynamic>> _gallery = [];
  int _total = 0;
  int _page = 1;
  static const int _pageSize = 12;

  bool _loading = true;
  bool _capturing = false;
  bool _liveMode = false;
  String? _error;

  // Lightbox
  String? _lightboxUrl;

  Timer? _liveTimer;

  // ── Lifecycle ─────────────────────────────────────────────────────────────
  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  @override
  void dispose() {
    _liveTimer?.cancel();
    super.dispose();
  }

  // ── Data helpers ──────────────────────────────────────────────────────────
  String get _baseUrl => AppConfig.baseUrl;

  String _imageUrl(String relUrl) => '$_baseUrl$relUrl';

  Future<void> _loadAll() async {
    setState(() => _loading = true);
    await Future.wait([_fetchLatest(), _fetchGallery(1)]);
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _fetchLatest() async {
    try {
      final res = await http
          .get(Uri.parse('$_baseUrl/api/v1/camera/latest'))
          .timeout(const Duration(seconds: 10));
      if (!mounted) return;
      if (res.statusCode == 200) {
        setState(() {
          _latest = json.decode(res.body) as Map<String, dynamic>;
          _error = null;
        });
      } else if (res.statusCode == 404) {
        setState(() => _latest = null);
      } else {
        setState(
          () => _error = 'Failed to load latest image (${res.statusCode})',
        );
      }
    } catch (e) {
      if (mounted) setState(() => _error = 'Cannot reach camera API');
    }
  }

  Future<void> _fetchGallery(int page) async {
    try {
      final res = await http
          .get(
            Uri.parse(
              '$_baseUrl/api/v1/camera/list?page=$page&page_size=$_pageSize',
            ),
          )
          .timeout(const Duration(seconds: 10));
      if (!mounted) return;
      if (res.statusCode == 200) {
        final data = json.decode(res.body) as Map<String, dynamic>;
        setState(() {
          _gallery = (data['images'] as List).cast<Map<String, dynamic>>();
          _total = data['total'] as int;
          _page = page;
        });
      }
    } catch (_) {
      // non-critical
    }
  }

  // ── Actions ───────────────────────────────────────────────────────────────
  void _toggleLive() {
    setState(() => _liveMode = !_liveMode);
    if (_liveMode) {
      _liveTimer = Timer.periodic(const Duration(seconds: 3), (_) {
        _fetchLatest();
        _fetchGallery(1);
      });
    } else {
      _liveTimer?.cancel();
    }
  }

  Future<void> _captureNow() async {
    setState(() => _capturing = true);
    try {
      final res = await http
          .post(Uri.parse('$_baseUrl/api/v1/camera/capture'))
          .timeout(const Duration(seconds: 10));
      if (res.statusCode == 200) {
        // Pi needs ~3–4 s to capture and upload
        await Future.delayed(const Duration(seconds: 4));
        await _fetchLatest();
        await _fetchGallery(1);
      } else {
        setState(() => _error = 'Capture trigger failed (${res.statusCode})');
      }
    } catch (e) {
      setState(() => _error = 'Cannot reach camera API');
    } finally {
      if (mounted) setState(() => _capturing = false);
    }
  }

  Future<void> _deleteImage(String filename) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Delete image?'),
        content: Text(filename),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );
    if (ok != true) return;

    try {
      await http
          .delete(Uri.parse('$_baseUrl/api/v1/camera/image/$filename'))
          .timeout(const Duration(seconds: 10));
      setState(() {
        _gallery.removeWhere((img) => img['filename'] == filename);
        _total = (_total - 1).clamp(0, 9999);
        if (_latest?['filename'] == filename) _latest = null;
      });
    } catch (_) {
      setState(() => _error = 'Delete failed');
    }
  }

  // ── Format helpers ────────────────────────────────────────────────────────
  String _formatDate(String iso) {
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day.toString().padLeft(2, '0')}/'
          '${dt.month.toString().padLeft(2, '0')}/'
          '${dt.year}  '
          '${dt.hour.toString().padLeft(2, '0')}:'
          '${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return iso;
    }
  }

  String _formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  // ── Build ─────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Plant Camera'),
        actions: [
          // Live toggle
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: TextButton.icon(
              onPressed: _toggleLive,
              icon: Icon(
                _liveMode ? Icons.wifi : Icons.wifi_off,
                size: 16,
                color: _liveMode ? AppColors.emerald500 : Colors.grey,
              ),
              label: Text(
                _liveMode ? 'Live' : 'Live off',
                style: TextStyle(
                  color: _liveMode ? AppColors.emerald500 : Colors.grey,
                  fontSize: 12,
                ),
              ),
            ),
          ),
          IconButton(
            icon: _loading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh),
            onPressed: _loadAll,
            tooltip: 'Refresh',
          ),
        ],
      ),

      // ── FAB: Capture now ───────────────────────────────────────────────
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _capturing ? null : _captureNow,
        backgroundColor: _capturing ? Colors.grey : AppColors.emerald500,
        icon: _capturing
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: Colors.white,
                ),
              )
            : const Icon(Icons.camera_alt, color: Colors.white),
        label: Text(
          _capturing ? 'Capturing…' : 'Capture Now',
          style: const TextStyle(color: Colors.white),
        ),
      ),

      body: _buildBody(isDark),

      // ── Lightbox overlay ───────────────────────────────────────────────
    );
  }

  Widget _buildBody(bool isDark) {
    return Stack(
      children: [
        RefreshIndicator(
          onRefresh: _loadAll,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Error banner
              if (_error != null) _errorBanner(),

              // Latest image
              _latestCard(isDark),

              const SizedBox(height: 16),

              // Status card
              _statusCard(isDark),

              const SizedBox(height: 16),

              // Gallery
              _gallerySection(isDark),

              // Pagination
              if (_total > _pageSize) _pagination(),

              const SizedBox(height: 80), // FAB clearance
            ],
          ),
        ),

        // Lightbox
        if (_lightboxUrl != null) _lightbox(),
      ],
    );
  }

  // ── Widgets ───────────────────────────────────────────────────────────────

  Widget _errorBanner() {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.red.shade900.withValues(alpha: 0.3),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.red.shade400.withValues(alpha: 0.5)),
      ),
      child: Row(
        children: [
          const Icon(Icons.error_outline, color: Colors.redAccent, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _error!,
              style: const TextStyle(color: Colors.redAccent, fontSize: 13),
            ),
          ),
          GestureDetector(
            onTap: () => setState(() => _error = null),
            child: const Icon(Icons.close, size: 16, color: Colors.redAccent),
          ),
        ],
      ),
    );
  }

  Widget _latestCard(bool isDark) {
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Latest Capture',
                  style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                ),
                if (_liveMode)
                  Row(
                    children: [
                      const SizedBox(width: 8, height: 8, child: _PulseDot()),
                      const SizedBox(width: 5),
                      Text(
                        'Live',
                        style: TextStyle(
                          fontSize: 11,
                          color: AppColors.emerald500,
                        ),
                      ),
                    ],
                  ),
              ],
            ),
          ),

          // Image
          if (_latest != null)
            GestureDetector(
              onTap: () => setState(
                () => _lightboxUrl = _imageUrl(_latest!['url'] as String),
              ),
              child: CachedNetworkImage(
                imageUrl: _imageUrl(_latest!['url'] as String),
                height: 220,
                width: double.infinity,
                fit: BoxFit.cover,
                placeholder: (_, __) => Container(
                  height: 220,
                  color: Colors.grey.shade800,
                  child: const Center(child: CircularProgressIndicator()),
                ),
                errorWidget: (_, __, ___) => Container(
                  height: 220,
                  color: Colors.grey.shade800,
                  child: const Center(
                    child: Icon(Icons.broken_image, size: 40),
                  ),
                ),
              ),
            )
          else
            Container(
              height: 180,
              color: isDark ? const Color(0xFF1A1F2E) : Colors.grey.shade100,
              child: const Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      Icons.camera_alt_outlined,
                      size: 40,
                      color: Colors.grey,
                    ),
                    SizedBox(height: 8),
                    Text(
                      'No images yet',
                      style: TextStyle(color: Colors.grey, fontSize: 13),
                    ),
                  ],
                ),
              ),
            ),

          // Meta
          if (_latest != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _MetaRow(
                    label: 'Captured',
                    value: _formatDate(_latest!['captured_at'] as String),
                  ),
                  _MetaRow(
                    label: 'Size',
                    value: _formatBytes(
                      (_latest!['size_bytes'] as num).toInt(),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _statusCard(bool isDark) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Camera Status',
              style: TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
            ),
            const SizedBox(height: 12),
            _StatusRow(
              label: 'Camera service',
              value: _latest != null ? 'Online' : 'No data',
              ok: _latest != null,
            ),
            _StatusRow(
              label: 'Live refresh',
              value: _liveMode ? 'Active (3 s)' : 'Off',
              ok: _liveMode,
            ),
            _StatusRow(label: 'Total images', value: '$_total', ok: _total > 0),
            if (_latest != null)
              _StatusRow(
                label: 'Last capture',
                value: _formatDate(_latest!['captured_at'] as String),
                ok: true,
              ),
            const SizedBox(height: 10),
            Text(
              'Pi camera captures every 5 min automatically.\n'
              'Tap "Capture Now" for an on-demand photo via MQTT.\n'
              'Toggle Live to auto-refresh every 3 s.',
              style: TextStyle(
                fontSize: 11,
                color: isDark ? Colors.grey.shade500 : Colors.grey.shade600,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _gallerySection(bool isDark) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Gallery',
              style: TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
            ),
            Text(
              '$_total image${_total == 1 ? '' : 's'}',
              style: TextStyle(
                fontSize: 12,
                color: isDark ? Colors.grey.shade500 : Colors.grey.shade600,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        if (_gallery.isEmpty)
          Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 24),
              child: Text(
                'No images yet.',
                style: TextStyle(color: Colors.grey.shade500),
              ),
            ),
          )
        else
          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 3,
              crossAxisSpacing: 8,
              mainAxisSpacing: 8,
            ),
            itemCount: _gallery.length,
            itemBuilder: (_, i) {
              final img = _gallery[i];
              final url = _imageUrl(img['url'] as String);
              return GestureDetector(
                onTap: () => setState(() => _lightboxUrl = url),
                onLongPress: () => _deleteImage(img['filename'] as String),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      CachedNetworkImage(
                        imageUrl: url,
                        fit: BoxFit.cover,
                        placeholder: (_, __) =>
                            Container(color: Colors.grey.shade800),
                        errorWidget: (_, __, ___) => Container(
                          color: Colors.grey.shade800,
                          child: const Icon(
                            Icons.broken_image,
                            size: 24,
                            color: Colors.grey,
                          ),
                        ),
                      ),
                      Positioned(
                        bottom: 0,
                        left: 0,
                        right: 0,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 4,
                            vertical: 3,
                          ),
                          decoration: const BoxDecoration(
                            gradient: LinearGradient(
                              begin: Alignment.bottomCenter,
                              end: Alignment.topCenter,
                              colors: [Colors.black87, Colors.transparent],
                            ),
                          ),
                          child: Text(
                            _formatDate(img['captured_at'] as String),
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 8,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
      ],
    );
  }

  Widget _pagination() {
    final totalPages = (_total / _pageSize).ceil();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          TextButton(
            onPressed: _page > 1 ? () => _fetchGallery(_page - 1) : null,
            child: const Text('← Prev'),
          ),
          const SizedBox(width: 8),
          Text('$_page / $totalPages', style: const TextStyle(fontSize: 13)),
          const SizedBox(width: 8),
          TextButton(
            onPressed: _page < totalPages
                ? () => _fetchGallery(_page + 1)
                : null,
            child: const Text('Next →'),
          ),
        ],
      ),
    );
  }

  Widget _lightbox() {
    return GestureDetector(
      onTap: () => setState(() => _lightboxUrl = null),
      child: Container(
        color: Colors.black.withValues(alpha: 0.9),
        child: Stack(
          children: [
            Center(
              child: InteractiveViewer(
                child: CachedNetworkImage(
                  imageUrl: _lightboxUrl!,
                  fit: BoxFit.contain,
                  placeholder: (_, __) =>
                      const CircularProgressIndicator(color: Colors.white),
                  errorWidget: (_, __, ___) => const Icon(
                    Icons.broken_image,
                    color: Colors.white,
                    size: 48,
                  ),
                ),
              ),
            ),
            Positioned(
              top: 16,
              right: 16,
              child: GestureDetector(
                onTap: () => setState(() => _lightboxUrl = null),
                child: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.black54,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Icon(Icons.close, color: Colors.white, size: 20),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Small helpers ─────────────────────────────────────────────────────────────

class _MetaRow extends StatelessWidget {
  const _MetaRow({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Text(
            '$label: ',
            style: const TextStyle(fontSize: 12, color: Colors.grey),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontSize: 12),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }
}

class _StatusRow extends StatelessWidget {
  const _StatusRow({
    required this.label,
    required this.value,
    required this.ok,
  });
  final String label;
  final String value;
  final bool ok;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 13, color: Colors.grey)),
          Text(
            value,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: ok ? AppColors.emerald500 : Colors.grey,
            ),
          ),
        ],
      ),
    );
  }
}

/// Simple animated pulsing dot for the Live indicator.
class _PulseDot extends StatefulWidget {
  const _PulseDot();

  @override
  State<_PulseDot> createState() => _PulseDotState();
}

class _PulseDotState extends State<_PulseDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 900),
  )..repeat(reverse: true);
  late final Animation<double> _opacity = Tween<double>(
    begin: 0.3,
    end: 1.0,
  ).animate(_ctrl);

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return FadeTransition(
      opacity: _opacity,
      child: const DecoratedBox(
        decoration: BoxDecoration(
          color: AppColors.emerald500,
          shape: BoxShape.circle,
        ),
        child: SizedBox(width: 8, height: 8),
      ),
    );
  }
}
