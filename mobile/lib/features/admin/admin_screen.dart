import 'package:flutter/material.dart';

import 'admin_reports_screen.dart';
import 'admin_facilities_screen.dart';
import 'admin_knowledge_screen.dart';
import 'admin_hotspot_screen.dart';

class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key});

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Admin Panel',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 20,
          ),
        ),
        automaticallyImplyLeading: false,
        bottom: TabBar(
          controller: _tabController,
          labelColor: const Color(0xFF1E3F28),
          unselectedLabelColor: Colors.grey,
          indicatorColor: const Color(0xFF1E3F28),
          indicatorWeight: 3,
          labelStyle: const TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 13,
          ),
          tabs: const [
            Tab(icon: Icon(Icons.article_outlined, size: 20), text: 'Laporan'),
            Tab(
                icon: Icon(Icons.location_city_outlined, size: 20),
                text: 'Fasilitas'),
            Tab(
                icon: Icon(Icons.menu_book_outlined, size: 20),
                text: 'Knowledge'),
            Tab(
                icon: Icon(Icons.whatshot_outlined, size: 20),
                text: 'Hotspot'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          AdminReportsScreen(),
          AdminFacilitiesScreen(),
          AdminKnowledgeScreen(),
          AdminHotspotScreen(),
        ],
      ),
    );
  }
}
