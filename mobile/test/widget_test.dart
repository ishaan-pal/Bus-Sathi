import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:haryana_roadways/main.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('App loads smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const BusSaathiApp());
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));

    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
