from flask import session

from models import Users


def is_user_logged_in():
    return 'user_id' in session


def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return Users.query.get(user_id)
    return None


def set_user_in_session(user_id=None, user=None, logout=False):
    if logout:
        session.pop('user', None)
        session.pop('user_id', None)
    elif user_id is not None:
        session['user_id'] = user_id
        session.pop('user', None)
    elif user is not None:
        session['user'] = user
        session.pop('user_id', None)
