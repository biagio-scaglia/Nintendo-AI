import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/chat_provider.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => ChatProvider(),
      child: MaterialApp(
        title: 'Nintendo AI Assistant',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme(
            brightness: Brightness.light,
            primary: const Color(0xFFE60012), // Rosso Nintendo
            onPrimary: Colors.white,
            secondary: const Color(0xFF1E1E1E), // Nero Nintendo
            onSecondary: Colors.white,
            tertiary: const Color(0xFF0066CC), // Blu Nintendo
            onTertiary: Colors.white,
            error: const Color(0xFFE60012),
            onError: Colors.white,
            surface: Colors.white,
            onSurface: const Color(0xFF1E1E1E),
            surfaceContainerHighest: const Color(0xFFF5F5F5),
            outline: const Color(0xFFE0E0E0),
          ),
          useMaterial3: true,
          fontFamily: 'Roboto',
          typography: Typography.material2021(),
          appBarTheme: const AppBarTheme(
            elevation: 0,
            centerTitle: false,
            backgroundColor: Color(0xFFE60012),
            foregroundColor: Colors.white,
            titleTextStyle: TextStyle(
              color: Colors.white,
              fontSize: 20,
              fontWeight: FontWeight.bold,
              letterSpacing: 0.5,
            ),
          ),
          cardTheme: CardThemeData(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              elevation: 2,
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: Colors.grey.shade100,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(28),
              borderSide: BorderSide.none,
            ),
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 20,
              vertical: 14,
            ),
          ),
        ),
        home: const HomeScreen(),
      ),
    );
  }
}
