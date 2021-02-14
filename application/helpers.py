#!/usr/bin/env python3
from flask import request, url_for, jsonify
import jwt
from functools import wraps
from werkzeug.exceptions import HTTPException
from application.api.users.User import User
from application.api.users.UserSchema import user_schema
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def verify_token(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        # Get the access token from the header
        # auth_header = request.headers.get('Authorization')
        # if auth_header is None:
        #     return {"message": "Token is missing"}, 401
        # access_token = auth_header.split(" ")[1]
        # if access_token:
        # Attempt to decode the token and get the User ID
        # user_id = User.decode_token(access_token)
        token = None
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if token is None:
            return {"message": "Token is missing"}, 401
        try:
            data = jwt.decode(token, 'SECRET_KEY')  # app.config['SECRET_KEY']
            # current_user = User.query.filter_by(username=data['username']).first()
            # current_user = data
            print('here')
            current_user = User.get_by_username('ncthanh')
            print('verify token', user_schema.dump(current_user))
            # current_user = User.get_by_id('38c1bba1-b13c-434c-bb32-8c32c99c2f8c')
            print('here 1')
            return f(user_schema.dump(current_user), *args, **kwargs)
        except Exception as e:
            return {"message": "Invalid user"}, 401
    return decorator


def paginate(schema=None, max_per_page=100):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', max_per_page,
                                            type=int),
                           max_per_page)

            query = func(*args, **kwargs)
            p = query.paginate(page, per_page)

            meta = {
                'page': page,
                'per_page': per_page,
                'total': p.total,
                'pages': p.pages,
            }

            links = {}
            if p.has_next:
                links['next'] = url_for(request.endpoint, page=p.next_num,
                                        per_page=per_page, **kwargs)
            if p.has_prev:
                links['prev'] = url_for(request.endpoint, page=p.prev_num,
                                        per_page=per_page, **kwargs)
            links['first'] = url_for(request.endpoint, page=1,
                                     per_page=per_page, **kwargs)
            links['last'] = url_for(request.endpoint, page=p.pages,
                                    per_page=per_page, **kwargs)

            meta['links'] = links
            result = {
                'items': p.items,
                'meta': meta
            }

            return schema.dump(result), 200
        return wrapped
    return decorator


# def standardize_api_response(function):
#     """ Creates a standardized response. This function should be used as a deco
#     rator.
#     use @helpers.standardize_api_response above the function
#     :function: The function decorated should return a dict with one of
#     the keys  bellow:
#         success -> GET, 200
#         error -> Bad Request, 400
#         created -> POST, 201
#         updated -> PUT, 200
#         deleted -> DELETE, 200
#         no-data -> No Content, 204
#
#     :returns: json.dumps(response), staus code
#     """
#
#     available_result_keys = [
#         'success', 'error', 'created', 'updated', 'deleted', 'no-data']
#
#     status_code_and_descriptions = {
#         'success': (200, 'Successful Operation'),
#         'error': (400, 'Bad Request'),
#         'created': (201, 'Successfully created'),
#         'updated': (200, 'Successfully updated'),
#         'deleted': (200, 'Successfully deleted'),
#         'no-data': (204, '')
#     }
#
#     @functools.wraps(function)
#     def make_response(*args, **kwargs):
#
#         result = function(*args, **kwargs)
#
#         if not set(available_result_keys) & set(result):
#             raise ValueError('Invalid result key.')
#
#         status_code, description = status_code_and_descriptions[
#             next(iter(result.keys()))
#         ]
#
#         status_code = ('status_code', status_code)
#         description = (
#             ('description', description) if status_code[1] != 400 else
#             ('error', description)
#         )
#         data = (
#             ('data', next(iter(result.values()))) if status_code[1] != 204 else
#             ('data', '')
#         )
#
#         return json.dumps(collections.OrderedDict([
#             status_code, description, data])), status_code[-1]
#
#     return make_response


def get_error_response(e):
    logger.exception(e)
    code = 500
    message = str(e)
    if isinstance(e, HTTPException):
        code = e.code
    if hasattr(e, 'description'):
        message = e.description
    return {
        'success': False,
        'type': e.__class__.__name__,
        'message': message
    }, code
