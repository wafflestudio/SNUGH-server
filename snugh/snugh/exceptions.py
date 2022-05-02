"""
Custom Errors
"""

from rest_framework import exceptions, status


class BaseError(exceptions.APIException):
    pass

class ServerError(BaseError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = '서버 에러입니다. 서버 관리자에게 문의 바랍니다.'
    default_code = 'E000'

class DatabaseError(BaseError):
    status_code = status.HTTP_409_CONFLICT
    default_detail = '데이터베이스 에러입니다. 서버 관리자에게 문의 바랍니다.'
    default_code = 'E001'

class AnonymousError(BaseError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = '로그인 후 다시 시도해주세요.'
    default_code = 'E101'

class AuthentificationFailed(BaseError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '아이디 또는 비밀번호를 확인해주세요.'
    default_code = 'E102'

class NotAuthenticated(BaseError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = '인증 토큰이 전달되지 않았습니다.'
    default_code = 'E103'

class ExpiredToken(BaseError):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = '토큰이 만료되었습니다.'
    default_code = 'E104'

class SocialLoginError(BaseError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '소셜 로그인 오류입니다.'
    default_code = 'E105'

class AlreadyLogin(BaseError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '이미 로그인 되어있습니다.'
    default_code = 'E106'

class FieldError(BaseError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '입력이 잘못 되었습니다.'
    default_code = 'E201'

class DuplicationError(BaseError):
    status_code = status.HTTP_409_CONFLICT
    default_detail = '이미 존재하는 값입니다.'
    default_code = 'E202'

class NotAllowed(BaseError):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = '권한이 없습니다.'
    default_code = 'E203'

class NotFound(BaseError):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Not found.'
    default_code = 'E204'

class NotOwner(BaseError):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '권한이 없습니다.'
    default_code = 'E205'