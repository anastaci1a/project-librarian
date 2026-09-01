# dep

from functools import wraps


# helper(s)

def requires_active(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        self._require_active()
        return method(self, *args, **kwargs)
    return guarded