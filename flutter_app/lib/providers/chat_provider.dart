import 'package:flutter/foundation.dart';
import '../models/message.dart';
import '../models/chat_response.dart';
import '../services/nintendo_api_service.dart';

class ChatProvider with ChangeNotifier {
  final NintendoApiService _apiService = NintendoApiService();
  final List<Message> _messages = [];
  bool _isLoading = false;
  String? _error;

  List<Message> get messages => _messages;
  bool get isLoading => _isLoading;
  String? get error => _error;

  ChatProvider() {
    // Messaggio di benvenuto iniziale
    _messages.add(Message(
      role: 'assistant',
      content: 'Ciao! Sono il tuo assistente Nintendo AI. Posso aiutarti a trovare giochi, darti informazioni sui giochi e consigliarti in base alle tue preferenze. Come posso aiutarti?',
    ));
  }

  Future<void> sendMessage(String content) async {
    if (content.trim().isEmpty) return;

    // Aggiungi il messaggio dell'utente
    final userMessage = Message(role: 'user', content: content);
    _messages.add(userMessage);
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // Invia la richiesta all'API
      final response = await _apiService.sendChat(_messages);

      // Aggiungi la risposta dell'assistente con info e recommendedGame se presenti
      _messages.add(Message(
        role: 'assistant',
        content: response.reply,
        info: response.info,
        recommendedGame: response.recommendedGame,
      ));

      _error = null;
    } catch (e) {
      _error = 'Errore: ${e.toString()}';
      _messages.add(Message(
        role: 'assistant',
        content: 'Mi dispiace, c\'è stato un errore nella comunicazione con il server. Assicurati che l\'API sia in esecuzione su localhost:8000',
      ));
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void clearChat() {
    _messages.clear();
    _messages.add(Message(
      role: 'assistant',
      content: 'Ciao! Sono il tuo assistente Nintendo AI. Posso aiutarti a trovare giochi, darti informazioni sui giochi e consigliarti in base alle tue preferenze. Come posso aiutarti?',
    ));
    _error = null;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }

  Future<void> deepenMessage(int messageIndex) async {
    if (messageIndex < 0 || messageIndex >= _messages.length) return;
    
    final message = _messages[messageIndex];
    if (message.role != 'assistant') return;

    // Trova il messaggio dell'utente precedente per capire l'argomento
    String? topic;
    for (int i = messageIndex - 1; i >= 0; i--) {
      if (_messages[i].role == 'user') {
        topic = _messages[i].content;
        break;
      }
    }

    // Costruisci il messaggio di approfondimento
    String deepenMessage;
    if (topic != null && topic.isNotEmpty) {
      // Usa l'argomento originale per essere più specifico
      deepenMessage = "Approfondisci: $topic";
    } else {
      // Fallback generico
      deepenMessage = "Approfondisci";
    }

    // Invia il messaggio di approfondimento
    await sendMessage(deepenMessage);
  }
}

