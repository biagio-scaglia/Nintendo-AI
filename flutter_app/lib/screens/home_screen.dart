import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:radix_icons/radix_icons.dart';
import '../providers/chat_provider.dart';
import 'chat_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const _HomeTab(),
    const ChatScreen(),
    const _GamesTab(),
    const _ProfileTab(),
  ];

  void _navigateToTab(int index) {
    setState(() {
      _currentIndex = index;
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    
    return Scaffold(
      body: SafeArea(
        child: IndexedStack(
          index: _currentIndex,
          children: _screens,
        ),
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: colorScheme.surface,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: SafeArea(
          child: Container(
            height: 70,
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _NavItem(
                  icon: RadixIcons.home,
                  label: 'Home',
                  isSelected: _currentIndex == 0,
                  onTap: () => _navigateToTab(0),
                ),
                _NavItem(
                  icon: RadixIcons.chat_bubble,
                  label: 'Chat',
                  isSelected: _currentIndex == 1,
                  onTap: () => _navigateToTab(1),
                ),
                _NavItem(
                  icon: RadixIcons.gamepad,
                  label: 'Giochi',
                  isSelected: _currentIndex == 2,
                  onTap: () => _navigateToTab(2),
                ),
                _NavItem(
                  icon: RadixIcons.person,
                  label: 'Profilo',
                  isSelected: _currentIndex == 3,
                  onTap: () => _navigateToTab(3),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  final RadixIconData icon;
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _NavItem({
    required this.icon,
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    
    return Expanded(
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                RadixIcon(
                  icon,
                  size: 24,
                  color: isSelected
                      ? colorScheme.primary
                      : colorScheme.onSurface.withOpacity(0.6),
                ),
                const SizedBox(height: 4),
                Text(
                  label,
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: isSelected
                        ? colorScheme.primary
                        : colorScheme.onSurface.withOpacity(0.6),
                    fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _HomeTab extends StatelessWidget {
  const _HomeTab();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final size = MediaQuery.of(context).size;
    final isTablet = size.width > 600;

    return CustomScrollView(
      slivers: [
        SliverAppBar(
          expandedHeight: 200,
          floating: false,
          pinned: true,
          elevation: 0,
          backgroundColor: colorScheme.primary,
          flexibleSpace: FlexibleSpaceBar(
            title: const Text(
              'Nintendo AI',
              style: TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
            centerTitle: false,
            titlePadding: const EdgeInsets.only(left: 20, bottom: 16),
            background: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [
                    colorScheme.primary,
                    colorScheme.primary.withOpacity(0.8),
                  ],
                ),
              ),
              child: const Center(
                child: Text(
                  '🎮',
                  style: TextStyle(fontSize: 80),
                ),
              ),
            ),
          ),
        ),
        SliverPadding(
          padding: EdgeInsets.all(isTablet ? 24 : 16),
          sliver: SliverList(
            delegate: SliverChildListDelegate([
              _WelcomeCard(),
              const SizedBox(height: 24),
              _QuickActionsGrid(
                isTablet: isTablet,
                onChatTap: () {
                  final homeState = context.findAncestorStateOfType<_HomeScreenState>();
                  homeState?._navigateToTab(1);
                },
              ),
              const SizedBox(height: 24),
              _RecentGamesSection(),
            ]),
          ),
        ),
      ],
    );
  }
}

class _WelcomeCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: colorScheme.primaryContainer,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Benvenuto! 👋',
            style: theme.textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: colorScheme.onPrimaryContainer,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Sono il tuo assistente Nintendo AI. Posso aiutarti a trovare giochi, darti informazioni e consigliarti in base alle tue preferenze!',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: colorScheme.onPrimaryContainer.withOpacity(0.8),
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickActionsGrid extends StatelessWidget {
  final bool isTablet;
  final VoidCallback onChatTap;

  const _QuickActionsGrid({
    required this.isTablet,
    required this.onChatTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final crossAxisCount = isTablet ? 4 : 2;
    final spacing = isTablet ? 20.0 : 12.0;

    final actions = [
      _ActionItem(
        icon: RadixIcons.chat_bubble,
        label: 'Chat',
        color: Colors.blue,
        onTap: onChatTap,
      ),
      _ActionItem(
        icon: RadixIcons.magnifying_glass,
        label: 'Cerca Giochi',
        color: Colors.purple,
        onTap: () {},
      ),
      _ActionItem(
        icon: RadixIcons.star,
        label: 'Raccomandazioni',
        color: Colors.orange,
        onTap: () {},
      ),
      _ActionItem(
        icon: RadixIcons.info_circled,
        label: 'Info Giochi',
        color: Colors.green,
        onTap: () {},
      ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Azioni Rapide',
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: crossAxisCount,
            crossAxisSpacing: spacing,
            mainAxisSpacing: spacing,
            childAspectRatio: 1.1,
          ),
          itemCount: actions.length,
          itemBuilder: (context, index) => actions[index],
        ),
      ],
    );
  }
}

class _ActionItem extends StatelessWidget {
  final RadixIconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _ActionItem({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: color.withOpacity(0.2),
              width: 1,
            ),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              RadixIcon(
                icon,
                size: 32,
                color: color,
              ),
              const SizedBox(height: 8),
              Text(
                label,
                style: theme.textTheme.labelMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: color,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RecentGamesSection extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Giochi Popolari',
          style: theme.textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 16),
        SizedBox(
          height: 200,
          child: ListView(
            scrollDirection: Axis.horizontal,
            children: [
              _GameCard(
                title: 'The Legend of Zelda',
                subtitle: 'Breath of the Wild',
                color: Colors.green,
              ),
              const SizedBox(width: 12),
              _GameCard(
                title: 'Super Mario',
                subtitle: 'Odyssey',
                color: Colors.red,
              ),
              const SizedBox(width: 12),
              _GameCard(
                title: 'Animal Crossing',
                subtitle: 'New Horizons',
                color: Colors.orange,
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _GameCard extends StatelessWidget {
  final String title;
  final String subtitle;
  final Color color;

  const _GameCard({
    required this.title,
    required this.subtitle,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      width: 160,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            color,
            color.withOpacity(0.7),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            Text(
              title,
              style: theme.textTheme.titleMedium?.copyWith(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              subtitle,
              style: theme.textTheme.bodySmall?.copyWith(
                color: Colors.white.withOpacity(0.9),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _GamesTab extends StatelessWidget {
  const _GamesTab();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SafeArea(
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            RadixIcon(
              RadixIcons.gamepad,
              size: 64,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(
              'Giochi',
              style: theme.textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              'Sezione giochi in arrivo',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProfileTab extends StatelessWidget {
  const _ProfileTab();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SafeArea(
      child: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            RadixIcon(
              RadixIcons.person,
              size: 64,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(
              'Profilo',
              style: theme.textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              'Sezione profilo in arrivo',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurface.withOpacity(0.6),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

