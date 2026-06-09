import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../core/api/api_client.dart';
import '../../core/models/user_model.dart';
import 'auth_repository.dart';

part 'auth_state.dart';

class AuthCubit extends Cubit<AuthState> {
  AuthCubit(this._repository) : super(const AuthState.unknown());

  final AuthRepository _repository;

  Future<void> checkAuthStatus() async {
    emit(state.copyWith(status: AuthStatus.loading));
    try {
      final loggedIn = await _repository.isLoggedIn();
      if (!loggedIn) {
        emit(const AuthState.unauthenticated());
        return;
      }
      final profileComplete = await _repository.isProfileComplete();
      if (!profileComplete) {
        emit(const AuthState.needsProfile());
        return;
      }
      final user = await _repository.getMe();
      emit(AuthState.authenticated(user));
    } on ApiException catch (e) {
      await _repository.logout();
      emit(AuthState.unauthenticated(message: e.message));
    } catch (_) {
      await _repository.logout();
      emit(const AuthState.unauthenticated());
    }
  }

  Future<void> sendOtp(String mobile) async {
    emit(state.copyWith(status: AuthStatus.loading, errorMessage: null));
    try {
      final message = await _repository.sendOtp(mobile);
      emit(state.copyWith(
        status: AuthStatus.otpSent,
        mobile: mobile,
        successMessage: message,
      ));
    } on ApiException catch (e) {
      emit(state.copyWith(status: AuthStatus.failure, errorMessage: e.message));
    }
  }

  Future<void> verifyOtp(String otp) async {
    final mobile = state.mobile;
    if (mobile == null) return;
    emit(state.copyWith(status: AuthStatus.loading, errorMessage: null));
    try {
      final result = await _repository.verifyOtp(mobile, otp);
      if (!result.user.profileComplete) {
        emit(AuthState.needsProfile(user: result.user, mobile: mobile));
      } else {
        emit(AuthState.authenticated(result.user));
      }
    } on ApiException catch (e) {
      emit(state.copyWith(status: AuthStatus.failure, errorMessage: e.message));
    }
  }

  Future<void> completeProfile({
    required String name,
    required String dateOfBirth,
  }) async {
    emit(state.copyWith(status: AuthStatus.loading, errorMessage: null));
    try {
      final user = await _repository.completeProfile(
        name: name,
        dateOfBirth: dateOfBirth,
      );
      emit(AuthState.authenticated(user));
    } on ApiException catch (e) {
      emit(state.copyWith(status: AuthStatus.failure, errorMessage: e.message));
    }
  }

  Future<void> verifyAadhaar(String aadhaar) async {
    emit(state.copyWith(status: AuthStatus.loading, errorMessage: null));
    try {
      await _repository.verifyAadhaar(aadhaar);
      emit(state.copyWith(
        status: AuthStatus.aadhaarVerified,
        successMessage: 'Aadhaar verified successfully',
      ));
    } on ApiException catch (e) {
      emit(state.copyWith(status: AuthStatus.failure, errorMessage: e.message));
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

  Future<void> logout() async {
    await _repository.logout();
    emit(const AuthState.unauthenticated());
  }

  void clearMessages() {
    emit(state.copyWith(errorMessage: null, successMessage: null));
  }
}
