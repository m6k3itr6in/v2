def user_role_processor(request):
    from main.views import get_user_role
    if request.user.is_authenticated:
        return {'user_role': get_user_role(request.user)}
    return {'user_role': None}
