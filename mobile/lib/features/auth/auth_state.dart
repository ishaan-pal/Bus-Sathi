part of 'auth_cubit.dart';

enum AuthStatus {
  unknown,
  loading,
  unauthenticated,
  otpSent,
  needsProfile,
  authenticated,
  aadhaarVerified,
  failure,
}

class AuthState extends Equatable {
  const AuthState({
    required this.status,
    this.user,
    this.mobile,
    this.errorMessage,
    this.successMessage,
  });

  const AuthState.unknown() : this(status: AuthStatus.unknown);

  const AuthState.unauthenticated({String? message})
      : this(
          status: AuthStatus.unauthenticated,
          errorMessage: message,
        );

  const AuthState.needsProfile({UserModel? user, String? mobile})
      : this(
          status: AuthStatus.needsProfile,
          user: user,
          mobile: mobile,
        );

  const AuthState.authenticated(UserModel user)
      : this(status: AuthStatus.authenticated, user: user);

  final AuthStatus status;
  final UserModel? user;
  final String? mobile;
  final String? errorMessage;
  final String? successMessage;

  bool get isAuthenticated => status == AuthStatus.authenticated;

  AuthState copyWith({
    AuthStatus? status,
    UserModel? user,
    String? mobile,
    String? errorMessage,
    String? successMessage,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: user ?? this.user,
      mobile: mobile ?? this.mobile,
      errorMessage: errorMessage,
      successMessage: successMessage,
    );
  }

  @override
  List<Object?> get props => [status, user, mobile, errorMessage];
}
