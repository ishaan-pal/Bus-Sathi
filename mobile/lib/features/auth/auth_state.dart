part of 'auth_cubit.dart';

enum AuthStatus {
  ready,
  loading,
  authenticated,
}

class AuthState extends Equatable {
  const AuthState({
    required this.status,
    this.user,
    this.errorMessage,
    this.successMessage,
  });

  const AuthState.ready({String? message})
      : this(
          status: AuthStatus.ready,
          errorMessage: message,
        );

  const AuthState.authenticated(UserModel user)
      : this(status: AuthStatus.authenticated, user: user);

  final AuthStatus status;
  final UserModel? user;
  final String? errorMessage;
  final String? successMessage;

  bool get isAadhaarVerified => user?.aadhaarVerified ?? false;

  AuthState copyWith({
    AuthStatus? status,
    UserModel? user,
    String? errorMessage,
    String? successMessage,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: user ?? this.user,
      errorMessage: errorMessage,
      successMessage: successMessage,
    );
  }

  @override
  List<Object?> get props => [status, user, errorMessage];
}
