import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/router/app_router.dart';
import 'core/api/api_config.dart';
import 'core/theme/app_theme.dart';

void main() {
  ApiConfig.validate();
  LicenseRegistry.addLicense(() async* {
    final license = await rootBundle.loadString(
      'assets/fonts/Lato-LICENSE.txt',
    );
    yield LicenseEntryWithLineBreaks(['Lato'], license);
  });
  runApp(const ProviderScope(child: EcoTechApp()));
}

class EcoTechApp extends ConsumerWidget {
  const EcoTechApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'EcoTech',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      routerConfig: router,
    );
  }
}
