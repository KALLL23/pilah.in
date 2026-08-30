import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

class LocationResult {
  final double latitude;
  final double longitude;
  final String address;
  const LocationResult({
    required this.latitude,
    required this.longitude,
    required this.address,
  });
}

class LocationPicker extends StatefulWidget {
  final double initialLat;
  final double initialLng;
  const LocationPicker({
    super.key,
    this.initialLat = -6.9666,
    this.initialLng = 110.4196,
  });

  @override
  State<LocationPicker> createState() => _LocationPickerState();
}

class _LocationPickerState extends State<LocationPicker> {
  final _searchCtrl = TextEditingController();
  final _dio = Dio();
  Timer? _debounce;

  GoogleMapController? _mapController;
  LatLng? _selected;
  String _selectedAddress = '';
  bool _searching = false;
  String? _searchError;
  List<_PlaceResult> _predictions = [];
  final Set<Marker> _markers = {};

  @override
  void initState() {
    super.initState();
    _selected = LatLng(widget.initialLat, widget.initialLng);
    _updateMarker();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchCtrl.dispose();
    _mapController?.dispose();
    super.dispose();
  }

  void _updateMarker() {
    if (_selected == null) return;
    setState(() {
      _markers.clear();
      _markers.add(
        Marker(
          markerId: const MarkerId('picked'),
          position: _selected!,
          draggable: true,
          onDragEnd: (pos) => _onPicked(pos),
        ),
      );
    });
  }

  void _onPicked(LatLng pos) {
    setState(() {
      _selected = pos;
      _selectedAddress = '';
    });
    _updateMarker();
    _reverseGeocode(pos.latitude, pos.longitude);
  }

  Future<void> _reverseGeocode(double lat, double lng) async {
    try {
      final resp = await _dio.get(
        'https://nominatim.openstreetmap.org/reverse',
        queryParameters: {
          'lat': lat,
          'lon': lng,
          'format': 'json',
          'addressdetails': 1,
        },
        options: Options(
          headers: {'User-Agent': 'pilahin-app/1.0'},
        ),
      );
      if (resp.data != null && resp.data is Map) {
        setState(() {
          _selectedAddress = resp.data['display_name'] ?? '';
        });
      }
    } catch (_) {}
  }

  void _onSearchChanged(String query) {
    _debounce?.cancel();
    if (query.trim().length < 2) {
      setState(() {
        _predictions = [];
        _searchError = null;
      });
      return;
    }
    _debounce = Timer(const Duration(milliseconds: 400), () {
      _search(query);
    });
  }

  Future<void> _search(String query) async {
    setState(() {
      _searching = true;
      _searchError = null;
    });
    try {
      final resp = await _dio.get(
        'https://nominatim.openstreetmap.org/search',
        queryParameters: {
          'q': query,
          'format': 'json',
          'countrycodes': 'id',
          'limit': 8,
          'addressdetails': 1,
        },
        options: Options(
          headers: {'User-Agent': 'pilahin-app/1.0'},
        ),
      );
      final results = (resp.data as List?) ?? [];
      setState(() {
        _predictions = results
            .map((r) => _PlaceResult(
                  displayName: r['display_name'] ?? '',
                  lat: double.tryParse(r['lat']?.toString() ?? '') ?? 0,
                  lng: double.tryParse(r['lon']?.toString() ?? '') ?? 0,
                ))
            .toList();
        _searching = false;
      });
    } catch (e) {
      setState(() {
        _predictions = [];
        _searching = false;
        _searchError = 'Gagal mencari lokasi';
      });
    }
  }

  void _selectPrediction(_PlaceResult pred) {
    setState(() {
      _predictions = [];
      _searchCtrl.text = pred.displayName;
      _selected = LatLng(pred.lat, pred.lng);
      _selectedAddress = pred.displayName;
      _searchError = null;
    });
    _updateMarker();
    _mapController?.animateCamera(CameraUpdate.newLatLngZoom(_selected!, 16));
  }

  @override
  Widget build(BuildContext context) {
    const primaryGreen = Color(0xFF1E3F28);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Pilih Lokasi',
            style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: primaryGreen,
        foregroundColor: Colors.white,
        actions: [
          TextButton(
            onPressed: _selected == null
                ? null
                : () => Navigator.pop(
                      context,
                      LocationResult(
                        latitude: _selected!.latitude,
                        longitude: _selected!.longitude,
                        address: _selectedAddress,
                      ),
                    ),
            child: const Text('Pilih',
                style: TextStyle(
                    color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
      body: Stack(
        children: [
          GoogleMap(
            initialCameraPosition: CameraPosition(
              target: _selected!,
              zoom: 14,
            ),
            onMapCreated: (c) => _mapController = c,
            markers: _markers,
            onTap: (pos) => _onPicked(pos),
            myLocationEnabled: true,
            zoomControlsEnabled: false,
          ),
          Positioned(
            top: 8,
            left: 12,
            right: 12,
            child: Column(
              children: [
                Card(
                  elevation: 4,
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                  child: TextField(
                    controller: _searchCtrl,
                    onChanged: _onSearchChanged,
                    decoration: InputDecoration(
                      hintText: 'Cari lokasi...',
                      prefixIcon: const Icon(Icons.search),
                      suffixIcon: _searching
                          ? const Padding(
                              padding: EdgeInsets.all(12),
                              child: SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2)),
                            )
                          : _searchCtrl.text.isNotEmpty
                              ? IconButton(
                                  icon: const Icon(Icons.clear),
                                  onPressed: () {
                                    _searchCtrl.clear();
                                    setState(() {
                                      _predictions = [];
                                      _searchError = null;
                                    });
                                  },
                                )
                              : null,
                      border: InputBorder.none,
                      contentPadding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 14),
                    ),
                  ),
                ),
                if (_searchError != null)
                  Card(
                    margin: const EdgeInsets.only(top: 4),
                    color: Colors.red[50],
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        children: [
                          Icon(Icons.error_outline,
                              size: 18, color: Colors.red[400]),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              _searchError!,
                              style: TextStyle(
                                  fontSize: 12, color: Colors.red[600]),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                if (_predictions.isNotEmpty)
                  Card(
                    margin: const EdgeInsets.only(top: 4),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12)),
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxHeight: 200),
                      child: ListView.separated(
                        shrinkWrap: true,
                        itemCount: _predictions.length,
                        separatorBuilder: (_, __) =>
                            const Divider(height: 1),
                        itemBuilder: (ctx, i) {
                          final pred = _predictions[i];
                          return ListTile(
                            dense: true,
                            leading: const Icon(Icons.location_on,
                                size: 20, color: primaryGreen),
                            title: Text(pred.displayName,
                                style: const TextStyle(fontSize: 12),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis),
                            onTap: () => _selectPrediction(pred),
                          );
                        },
                      ),
                    ),
                  ),
              ],
            ),
          ),
          if (_selectedAddress.isNotEmpty)
            Positioned(
              bottom: 24,
              left: 16,
              right: 16,
              child: Card(
                elevation: 4,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Text(
                        _selectedAddress,
                        style: const TextStyle(
                            fontSize: 12, fontWeight: FontWeight.w500),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 4),
                      Text(
                        '${_selected!.latitude.toStringAsFixed(6)}, ${_selected!.longitude.toStringAsFixed(6)}',
                        style: TextStyle(
                            fontSize: 11, color: Colors.grey[500]),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          Positioned(
            bottom: 80,
            right: 16,
            child: FloatingActionButton.small(
              backgroundColor: Colors.white,
              onPressed: () async {
                try {
                  final loc = await Navigator.of(context)
                      .push<LatLng>(
                        MaterialPageRoute(
                          builder: (_) => const _CurrentLocationPage(),
                        ),
                      );
                  if (loc != null) {
                    setState(() {
                      _selected = loc;
                      _selectedAddress = '';
                    });
                    _updateMarker();
                    _mapController?.animateCamera(
                        CameraUpdate.newLatLngZoom(loc, 16));
                    _reverseGeocode(loc.latitude, loc.longitude);
                  }
                } catch (_) {}
              },
              child: const Icon(Icons.my_location, color: primaryGreen),
            ),
          ),
        ],
      ),
    );
  }
}

class _CurrentLocationPage extends StatelessWidget {
  const _CurrentLocationPage();

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: CircularProgressIndicator()),
    );
  }
}

class _PlaceResult {
  final String displayName;
  final double lat;
  final double lng;
  const _PlaceResult({
    required this.displayName,
    required this.lat,
    required this.lng,
  });
}
