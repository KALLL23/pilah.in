import 'package:flutter_test/flutter_test.dart';
import 'package:pilahin/main.dart';

void main() {
  testWidgets('renders the pilah.in application shell', (WidgetTester tester) async {
    await tester.pumpWidget(const PilahInApp());

    expect(find.text('pilah.in'), findsOneWidget);
  });
}
