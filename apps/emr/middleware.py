

from .models import AccessLog

class AccessLogMiddleware(object):

    def process_request(self, request):
        if request.user.is_authenticated() and not request.path.startswith('/list_of') and not request.path.endswith('/encounter/status'):
            access_log = AccessLog(user=request.user, summary=request.path)
            access_log.save()
