import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/communication/communication_data.dart';
import '../../data/communication/communication_repository.dart';

final communicationRepositoryProvider = Provider<CommunicationRepository>(
  (ref) => CommunicationRepository(),
);

final agendaProvider = FutureProvider.family<AgendaData, String>(
  (ref, id) => ref.read(communicationRepositoryProvider).buscarAgenda(id),
);

final conversasProvider = FutureProvider<List<ConversaData>>(
  (ref) => ref.read(communicationRepositoryProvider).listarConversas(),
);

final notificacoesProvider = FutureProvider<NotificacoesPaginaData>(
  (ref) => ref.read(communicationRepositoryProvider).listarNotificacoes(),
);

final badgesProvider = FutureProvider<BadgesData>(
  (ref) => ref.read(communicationRepositoryProvider).buscarBadges(),
);
