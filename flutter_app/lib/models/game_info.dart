class GameInfo {
  final String title;
  final String platform;
  final String description;
  final String gameplay;
  final String difficulty;
  final List<String> modes;
  final List<String> keywords;
  final String? imageUrl;

  GameInfo({
    required this.title,
    required this.platform,
    required this.description,
    required this.gameplay,
    required this.difficulty,
    required this.modes,
    required this.keywords,
    this.imageUrl,
  });

  factory GameInfo.fromJson(Map<String, dynamic> json) {
    final imageUrl = json['image_url'] as String?;
    if (imageUrl != null && imageUrl.isNotEmpty) {
      print('GameInfo.fromJson - image_url received: $imageUrl');
    }
    return GameInfo(
      title: json['title'] as String,
      platform: json['platform'] as String,
      description: json['description'] as String,
      gameplay: json['gameplay'] as String,
      difficulty: json['difficulty'] as String,
      modes: (json['modes'] as List<dynamic>).map((e) => e as String).toList(),
      keywords: (json['keywords'] as List<dynamic>).map((e) => e as String).toList(),
      imageUrl: imageUrl,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'platform': platform,
      'description': description,
      'gameplay': gameplay,
      'difficulty': difficulty,
      'modes': modes,
      'keywords': keywords,
    };
  }
}

