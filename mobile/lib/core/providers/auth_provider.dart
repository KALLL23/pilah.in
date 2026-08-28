import 'package:flutter_riverpod/flutter_riverpod.dart';

enum UserRole { user, admin }

class UserRoleNotifier extends Notifier<UserRole> {
  @override
  UserRole build() => UserRole.user;

  void setRole(UserRole role) {
    state = role;
  }
}

final userRoleProvider = NotifierProvider<UserRoleNotifier, UserRole>(() {
  return UserRoleNotifier();
});