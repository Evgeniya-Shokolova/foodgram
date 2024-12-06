from rest_framework.pagination import PageNumberPagination

from .constants import PAGENATION_SIZE


class PageLimitPaginator(PageNumberPagination):
    page_size = PAGENATION_SIZE
    page_size_query_param = 'limit'
