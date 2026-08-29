import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pilahin/main.dart';

void main() {
  testWidgets('renders the pilah.in application shell', (WidgetTester tester) async {
    await tester.pumpWidget(const ProviderScope(child: PilahInApp()));

    expect(find.text('pilah.in'), findsOneWidget);
  });
}
