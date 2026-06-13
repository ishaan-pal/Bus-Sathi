import 'package:flutter/material.dart';

/// Mixin for calling [setState] only when the widget is still mounted.
mixin SafeSetState<T extends StatefulWidget> on State<T> {
  void safeSetState(VoidCallback fn) {
    if (mounted) setState(fn);
  }
}

/// Ignore stale async results after [dispose] or a newer request.
mixin AsyncRequestGuard<T extends StatefulWidget> on State<T> {
  int _requestGeneration = 0;

  int beginRequest() => ++_requestGeneration;

  bool isCurrentRequest(int generation) =>
      mounted && generation == _requestGeneration;

  @override
  void dispose() {
    _requestGeneration++;
    super.dispose();
  }
}
