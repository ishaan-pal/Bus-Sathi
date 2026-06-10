import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../core/api/api_client.dart';
import '../../core/models/user_model.dart';
import 'auth_repository.dart';

part 'auth_state.dart';

class AuthCubit extends Cubit<AuthState> {
  AuthCubit(this._repository) : super(const AuthState.ready());

  final AuthRepository _repository;

  /// Opens the app immediately; guest session is created in the background.
  Future<void> initSession() async {
    try {
      final user = await _repository.ensureGuestSession();
      if (user != null) {
        emit(AuthState.authenticated(user));
      }
    } catch (_) {
      // Public features still work without a session.
    }
  }

  Future<void> ensureSession() async {
    if (state.user != null) return;

    emit(state.copyWith(status: AuthStatus.loading, errorMessage: null));
    try {
      final user = await _repository.ensureGuestSession();
      if (user != null) {
        emit(AuthState.authenticated(user));
      } else {
        emit(const AuthState.ready());
      }
    } on ApiException catch (e) {
      emit(AuthState.ready(message: e.message));
    } catch (_) {
      emit(const AuthState.ready());
    }
  }

  Future<bool> verifyAadhaar(String aadhaar) async {
    await ensureSession();
    if (state.user == null) {
      emit(state.copyWith(errorMessage: 'Unable to connect to server'));
      return false;
    }

    emit(state.copyWith(status: AuthStatus.loading, errorMessage: null));
    try {
      final user = await _repository.verifyAadhaar(aadhaar);
      emit(AuthState.authenticated(user));
      return true;
    } on ApiException catch (e) {
      emit(state.copyWith(
        status: AuthStatus.authenticated,
        user: state.user,
        errorMessage: e.message,
      ));
      return false;
    }
  }

  Future<void> refreshUser() async {
    try {
      final user = await _repository.getMe();
      emit(AuthState.authenticated(user));
    } on ApiException catch (e) {
      emit(state.copyWith(errorMessage: e.message));
    }
  }

  void clearMessages() {
    emit(state.copyWith(errorMessage: null, successMessage: null));
  }
}
