from line.models import Keyword, User
import logging
logger = logging.getLogger(__name__)

def from_rds(user_id):
    return User.objects.get(pk=user_id)

#TODO
def from_cache(user_id):
    return None
