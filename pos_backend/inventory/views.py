from django.shortcuts import get_object_or_404
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminOrReadOnly
from .models import Category, Product
from .serializers import CategorySerializer, ProductAdminSerializer, ProductPOSSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["code", "name"]
    ordering_fields = ["name", "selling_price", "stock"]

    def get_queryset(self):
        qs = Product.objects.select_related("category")
        if self.request.user.role != "ADMIN":
            qs = qs.filter(is_active=True)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category_id=category)
        return qs

    def get_serializer_class(self):
        if self.request.user.role == "ADMIN":
            return ProductAdminSerializer
        return ProductPOSSerializer

    @action(detail=False, methods=["get"], url_path=r"by-code/(?P<code>[^/.]+)")
    def by_code(self, request, code=None):
        """Búsqueda exacta por código de barras (lector de escáner)."""
        product = get_object_or_404(self.get_queryset(), code=code)
        return Response(self.get_serializer(product).data)
