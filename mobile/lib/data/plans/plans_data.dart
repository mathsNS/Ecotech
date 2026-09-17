class PlansData {
  const PlansData({
    required this.currentPlan,
    required this.plans,
    required this.featureFlags,
    required this.demoEnvironment,
  });

  factory PlansData.fromJson(Map<String, dynamic> json) => PlansData(
    currentPlan: json['plano_atual'] as String? ?? 'free',
    plans: (json['planos'] as List? ?? const [])
        .map((item) => PlanData.fromJson(Map<String, dynamic>.from(item as Map)))
        .toList(),
    featureFlags: Map<String, bool>.from(
      (json['feature_flags'] as Map?)?.map(
            (key, value) => MapEntry(key.toString(), value == true),
          ) ??
          const {},
    ),
    demoEnvironment: json['ambiente_demonstracao'] == true,
  );

  final String currentPlan;
  final List<PlanData> plans;
  final Map<String, bool> featureFlags;
  final bool demoEnvironment;
}

class PlanData {
  const PlanData({
    required this.id,
    required this.name,
    required this.monthlyPrice,
    required this.highlighted,
    required this.monthlyRequestLimit,
    required this.features,
    required this.featureFlags,
  });

  factory PlanData.fromJson(Map<String, dynamic> json) => PlanData(
    id: json['id'] as String? ?? '',
    name: json['nome'] as String? ?? '',
    monthlyPrice: (json['preco_mensal'] as num?)?.toDouble() ?? 0,
    highlighted: json['destaque'] == true,
    monthlyRequestLimit: (json['limite_solicitacoes_mes'] as num?)?.toInt(),
    features: List<String>.from(json['recursos'] as List? ?? const []),
    featureFlags: Map<String, bool>.from(
      (json['feature_flags'] as Map?)?.map(
            (key, value) => MapEntry(key.toString(), value == true),
          ) ??
          const {},
    ),
  );

  final String id;
  final String name;
  final double monthlyPrice;
  final bool highlighted;
  final int? monthlyRequestLimit;
  final List<String> features;
  final Map<String, bool> featureFlags;
}
