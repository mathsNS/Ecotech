class AppFormatters {
  AppFormatters._();

  static String moeda(dynamic valor) {
    final numero = (valor as num?)?.toDouble() ?? 0;
    final partes = numero.abs().toStringAsFixed(2).split('.');
    final inteiro = partes.first;
    final grupos = <String>[];
    for (var fim = inteiro.length; fim > 0; fim -= 3) {
      final inicio = fim > 3 ? fim - 3 : 0;
      grupos.insert(0, inteiro.substring(inicio, fim));
    }
    final sinal = numero < 0 ? '-' : '';
    return 'R\$ $sinal${grupos.join('.')},${partes.last}';
  }

  static String numero(dynamic valor, {int casas = 1}) {
    final numero = (valor as num?)?.toDouble() ?? 0;
    return numero.toStringAsFixed(casas).replaceAll('.', ',');
  }

  static String data(DateTime? valor, {bool curta = false}) {
    if (valor == null) return 'Data não informada';
    final dia = valor.day.toString().padLeft(2, '0');
    final mes = valor.month.toString().padLeft(2, '0');
    return curta ? '$dia/$mes' : '$dia/$mes/${valor.year}';
  }

  static String dataTexto(String valor) {
    final iso = DateTime.tryParse(valor);
    if (iso != null) return data(iso);
    final brasileira = RegExp(
      r'^(\d{2}/\d{2}/\d{4})(?:[ T](\d{2}:\d{2})(?::\d{2}(?:\.\d+)?)?)?$',
    ).firstMatch(valor);
    if (brasileira != null) return brasileira.group(1)!;
    if (RegExp(r'^\d{4}-\d{2}-\d{2}$').hasMatch(valor)) {
      final partes = valor.split('-');
      return '${partes[2]}/${partes[1]}/${partes[0]}';
    }
    return valor;
  }

  static String dataHoraTexto(String valor) {
    final iso = DateTime.tryParse(valor);
    if (iso != null) {
      final hora = iso.hour.toString().padLeft(2, '0');
      final minuto = iso.minute.toString().padLeft(2, '0');
      return '${data(iso)} $hora:$minuto';
    }
    final brasileira = RegExp(
      r'^(\d{2}/\d{2}/\d{4})(?:[ T](\d{2}:\d{2})(?::\d{2}(?:\.\d+)?)?)?$',
    ).firstMatch(valor);
    if (brasileira != null) {
      final hora = brasileira.group(2);
      return hora == null
          ? brasileira.group(1)!
          : '${brasileira.group(1)} $hora';
    }
    return valor;
  }

  static String documento(String? valor, String tipo) {
    final digitos = (valor ?? '').replaceAll(RegExp(r'\D'), '');
    if (tipo == 'cidadao' && digitos.length == 11) {
      return '${digitos.substring(0, 3)}.${digitos.substring(3, 6)}.'
          '${digitos.substring(6, 9)}-${digitos.substring(9)}';
    }
    if (tipo == 'empresa' && digitos.length == 14) {
      return '${digitos.substring(0, 2)}.${digitos.substring(2, 5)}.'
          '${digitos.substring(5, 8)}/${digitos.substring(8, 12)}-'
          '${digitos.substring(12)}';
    }
    return valor ?? 'Não informado';
  }
}
