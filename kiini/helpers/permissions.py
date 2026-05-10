# kiini/helpers/permissions.py 

def user_is_institution_admin(user):
    return user.role == 'INSTITUTION_ADMIN'


def user_is_staff(user):
    return user.role == 'STAFF'


def user_is_client(user):
    return user.role == 'CLIENT'