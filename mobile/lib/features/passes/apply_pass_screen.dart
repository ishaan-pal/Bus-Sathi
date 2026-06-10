import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';

import '../../core/api/api_client.dart';
import '../../core/models/pass_model.dart';
import '../../core/models/route_model.dart';
import '../../core/theme/app_colors.dart';
import '../../core/widgets/aadhaar_banner.dart';
import '../../core/widgets/hr_app_bar.dart';
import '../../core/widgets/loading_overlay.dart';
import '../buses/bus_repository.dart';
import 'pass_repository.dart';

class ApplyPassScreen extends StatefulWidget {
  const ApplyPassScreen({super.key});

  @override
  State<ApplyPassScreen> createState() => _ApplyPassScreenState();
}

class _ApplyPassScreenState extends State<ApplyPassScreen> {
  late final PassRepository _passRepo;
  late final BusRepository _busRepo;

  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _institutionController = TextEditingController();
  final _studentIdController = TextEditingController();

  String _passType = 'monthly';
  DateTime? _dob;
  List<RouteModel> _routes = [];
  String? _routeId;
  String? _fromStop;
  String? _toStop;
  bool _loading = false;
  bool _loadingRoutes = true;

  PassApplicationModel? _application;
  final Map<String, String> _uploadedDocs = {};
  final _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _passRepo = PassRepository(ApiClient());
    _busRepo = BusRepository(ApiClient());
    _loadRoutes();
  }

  @override
  void dispose() {
    _nameController.dispose();
    _institutionController.dispose();
    _studentIdController.dispose();
    super.dispose();
  }

  Future<void> _loadRoutes() async {
    try {
      final routes = await _busRepo.getAllRoutes();
      setState(() {
        _routes = routes;
        _loadingRoutes = false;
      });
    } catch (_) {
      setState(() => _loadingRoutes = false);
    }
  }

  Future<void> _pickDob() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime(now.year - 20),
      firstDate: DateTime(now.year - 120),
      lastDate: now.subtract(const Duration(days: 1)),
    );
    if (picked != null) setState(() => _dob = picked);
  }

  Future<void> _apply() async {
    if (!(_formKey.currentState?.validate() ?? false) || _dob == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please fill all required fields')),
      );
      return;
    }
    final ok = await ensureAadhaarVerified(context);
    if (!ok || !mounted) return;
    setState(() => _loading = true);
    try {
      final app = await _passRepo.applyForPass(
        passType: _passType,
        applicantName: _nameController.text.trim(),
        applicantDob: DateFormat('yyyy-MM-dd').format(_dob!),
        routeId: _routeId,
        fromStop: _fromStop,
        toStop: _toStop,
        institutionName: _passType == 'student'
            ? _institutionController.text.trim()
            : null,
        studentIdNumber: _passType == 'student'
            ? _studentIdController.text.trim()
            : null,
      );
      setState(() {
        _application = app;
        _loading = false;
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Application submitted. Upload documents.')),
      );
    } on ApiException catch (e) {
      setState(() => _loading = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message)),
      );
    }
  }

  Future<void> _uploadDoc(String docType) async {
    if (_application == null) return;
    final file = await _picker.pickImage(source: ImageSource.gallery);
    if (file == null) return;
    setState(() => _loading = true);
    try {
      await _passRepo.uploadDocument(
        passId: _application!.passId,
        docType: docType,
        filePath: file.path,
        fileName: file.name,
      );
      setState(() {
        _uploadedDocs[docType] = file.name;
        _loading = false;
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$docType uploaded')),
      );
    } on ApiException catch (e) {
      setState(() => _loading = false);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.message)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    RouteModel? selectedRoute;
    if (_routeId != null) {
      for (final r in _routes) {
        if (r.id == _routeId) {
          selectedRoute = r;
          break;
        }
      }
    }
    final stops = selectedRoute?.stopNames ?? <String>[];

    return Scaffold(
      appBar: HrAppBar(
        title: 'Apply for Pass',
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
      ),
      body: Stack(
        children: [
          SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (_application == null) ...[
                    Text(
                      'Pass Type',
                      style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 8),
                    SegmentedButton<String>(
                      segments: const [
                        ButtonSegment(value: 'student', label: Text('Student')),
                        ButtonSegment(value: 'monthly', label: Text('Monthly')),
                        ButtonSegment(
                          value: 'senior_citizen',
                          label: Text('Senior'),
                        ),
                      ],
                      selected: {_passType},
                      onSelectionChanged: (s) =>
                          setState(() => _passType = s.first),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _nameController,
                      decoration: const InputDecoration(labelText: 'Applicant Name'),
                      validator: (v) =>
                          (v?.trim().length ?? 0) < 2 ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),
                    InkWell(
                      onTap: _pickDob,
                      child: InputDecorator(
                        decoration: const InputDecoration(labelText: 'Date of Birth'),
                        child: Text(
                          _dob != null
                              ? DateFormat('dd MMM yyyy').format(_dob!)
                              : 'Select date',
                        ),
                      ),
                    ),
                    if (_passType == 'student') ...[
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _institutionController,
                        decoration: const InputDecoration(
                          labelText: 'Institution Name',
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _studentIdController,
                        decoration: const InputDecoration(
                          labelText: 'Student ID',
                        ),
                      ),
                    ],
                    if (!_loadingRoutes) ...[
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: _routeId,
                        decoration: const InputDecoration(labelText: 'Route (optional)'),
                        items: _routes
                            .map((r) => DropdownMenuItem(
                                  value: r.id,
                                  child: Text('${r.routeNumber} - ${r.name}'),
                                ))
                            .toList(),
                        onChanged: (v) => setState(() {
                          _routeId = v;
                          _fromStop = null;
                          _toStop = null;
                        }),
                      ),
                      if (stops.isNotEmpty) ...[
                        const SizedBox(height: 12),
                        DropdownButtonFormField<String>(
                          value: _fromStop,
                          decoration: const InputDecoration(labelText: 'From Stop'),
                          items: stops
                              .map((s) =>
                                  DropdownMenuItem(value: s, child: Text(s)))
                              .toList(),
                          onChanged: (v) => setState(() => _fromStop = v),
                        ),
                        const SizedBox(height: 12),
                        DropdownButtonFormField<String>(
                          value: _toStop,
                          decoration: const InputDecoration(labelText: 'To Stop'),
                          items: stops
                              .map((s) =>
                                  DropdownMenuItem(value: s, child: Text(s)))
                              .toList(),
                          onChanged: (v) => setState(() => _toStop = v),
                        ),
                      ],
                    ],
                    const SizedBox(height: 24),
                    ElevatedButton(
                      onPressed: _loading ? null : _apply,
                      child: const Text('Submit Application'),
                    ),
                  ] else ...[
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Application Submitted',
                              style: GoogleFonts.poppins(
                                fontWeight: FontWeight.bold,
                                fontSize: 18,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text('Pass ID: ${_application!.passId}'),
                            Text('Status: ${_application!.status}'),
                            const SizedBox(height: 16),
                            Text(
                              'Upload Required Documents',
                              style: GoogleFonts.poppins(fontWeight: FontWeight.w600),
                            ),
                            const SizedBox(height: 8),
                            ..._application!.requiredDocuments.map((doc) {
                              final uploaded = _uploadedDocs.containsKey(doc);
                              return ListTile(
                                leading: Icon(
                                  uploaded ? Icons.check_circle : Icons.upload_file,
                                  color: uploaded ? AppColors.green : null,
                                ),
                                title: Text(doc.replaceAll('_', ' ')),
                                trailing: uploaded
                                    ? null
                                    : TextButton(
                                        onPressed: () => _uploadDoc(doc),
                                        child: const Text('Upload'),
                                      ),
                              );
                            }),
                            const SizedBox(height: 16),
                            ElevatedButton(
                              onPressed: () => context.push(
                                '/passes/status/${_application!.passId}',
                              ),
                              child: const Text('Check Status'),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          if (_loading) const LoadingOverlay(),
        ],
      ),
    );
  }
}
