import 'dart:async';

import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/stops_service.dart';
import '../theme/app_colors.dart';

/// Typeahead stop picker — user types and matching stations appear instantly.
class StopSearchField extends StatefulWidget {
  const StopSearchField({
    super.key,
    required this.label,
    required this.hint,
    required this.icon,
    required this.iconColor,
    required this.stopsService,
    required this.onSelected,
    this.onChanged,
    this.initialValue,
    this.excludeStops = const {},
  });

  final String label;
  final String hint;
  final IconData icon;
  final Color iconColor;
  final StopsService stopsService;
  final ValueChanged<String> onSelected;
  final ValueChanged<String>? onChanged;
  final String? initialValue;
  final Set<String> excludeStops;

  @override
  State<StopSearchField> createState() => _StopSearchFieldState();
}

class _StopSearchFieldState extends State<StopSearchField> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();

  List<String> _suggestions = [];
  bool _loading = false;
  bool _showSuggestions = false;
  Timer? _debounce;
  int _searchGeneration = 0;

  @override
  void initState() {
    super.initState();
    if (widget.initialValue != null) {
      _controller.text = widget.initialValue!;
    }
    _focusNode.addListener(_onFocusChange);
    _controller.addListener(_onTextChanged);
  }

  @override
  void didUpdateWidget(covariant StopSearchField oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.initialValue != oldWidget.initialValue &&
        widget.initialValue != _controller.text) {
      _controller.text = widget.initialValue ?? '';
    }
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _focusNode.dispose();
    _controller.dispose();
    super.dispose();
  }

  void _onFocusChange() {
    if (!_focusNode.hasFocus) {
      setState(() => _showSuggestions = false);
      return;
    }
    if (_controller.text.trim().isNotEmpty) {
      _scheduleSearch(_controller.text);
    }
  }

  void _onTextChanged() {
    widget.onChanged?.call(_controller.text);
    final query = _controller.text;
    if (query.trim().isEmpty) {
      setState(() {
        _suggestions = [];
        _showSuggestions = false;
        _loading = false;
      });
      return;
    }
    _scheduleSearch(query);
  }

  void _scheduleSearch(String query) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 200), () {
      _runSearch(query);
    });
  }

  Future<void> _runSearch(String query) async {
    final generation = ++_searchGeneration;
    setState(() {
      _loading = true;
      _showSuggestions = true;
    });

    // Show local matches immediately while API request is in flight.
    final local = widget.stopsService.filterLocal(
      query,
      exclude: widget.excludeStops,
    );
    if (generation == _searchGeneration && mounted) {
      setState(() => _suggestions = local);
    }

    final remote = await widget.stopsService.search(
      query,
      exclude: widget.excludeStops,
    );

    if (generation != _searchGeneration || !mounted) return;
    setState(() {
      _suggestions = remote.isNotEmpty ? remote : local;
      _loading = false;
      _showSuggestions = _focusNode.hasFocus && _controller.text.trim().isNotEmpty;
    });
  }

  void _select(String stop) {
    _controller.text = stop;
    widget.onSelected(stop);
    setState(() {
      _showSuggestions = false;
      _suggestions = [];
    });
    _focusNode.unfocus();
  }

  void _clear() {
    _controller.clear();
    setState(() {
      _suggestions = [];
      _showSuggestions = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
          TextField(
            controller: _controller,
            focusNode: _focusNode,
            textInputAction: TextInputAction.next,
            decoration: InputDecoration(
              labelText: widget.label,
              hintText: widget.hint,
              prefixIcon: Icon(widget.icon, color: widget.iconColor),
              suffixIcon: _loading
                  ? const Padding(
                      padding: EdgeInsets.all(12),
                      child: SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    )
                  : _controller.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear, size: 20),
                          onPressed: _clear,
                        )
                      : const Icon(Icons.search, color: AppColors.textSecondary),
            ),
            onTap: () {
              if (_controller.text.trim().isNotEmpty) {
                setState(() => _showSuggestions = true);
              }
            },
          ),
          if (_showSuggestions && _suggestions.isNotEmpty)
            _SuggestionsList(
              suggestions: _suggestions,
              onSelect: _select,
            )
          else if (_showSuggestions &&
              !_loading &&
              _controller.text.trim().isNotEmpty)
            _NoResults(query: _controller.text.trim()),
      ],
    );
  }
}

class _SuggestionsList extends StatelessWidget {
  const _SuggestionsList({
    required this.suggestions,
    required this.onSelect,
  });

  final List<String> suggestions;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 4,
      borderRadius: BorderRadius.circular(12),
      color: Colors.white,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxHeight: 220),
        child: ListView.separated(
          shrinkWrap: true,
          padding: EdgeInsets.zero,
          itemCount: suggestions.length,
          separatorBuilder: (_, __) => Divider(
            height: 1,
            color: Colors.grey.shade200,
          ),
          itemBuilder: (context, index) {
            final stop = suggestions[index];
            return ListTile(
              dense: true,
              leading: const Icon(
                Icons.location_on_outlined,
                color: AppColors.deepBlue,
                size: 20,
              ),
              title: Text(
                stop,
                style: GoogleFonts.poppins(fontSize: 14),
              ),
              onTap: () => onSelect(stop),
            );
          },
        ),
      ),
    );
  }
}

class _NoResults extends StatelessWidget {
  const _NoResults({required this.query});

  final String query;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Text(
        'No stations matching "$query"',
        style: GoogleFonts.poppins(
          fontSize: 13,
          color: AppColors.textSecondary,
        ),
      ),
    );
  }
}
