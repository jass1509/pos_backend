from django.db import IntegrityError
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsAdminRole
from .models import Sale, Shift
from .serializers import (CloseShiftSerializer, OpenShiftSerializer, SaleCreateSerializer,
                          SaleSerializer, ShiftSerializer)
from . import services


def _open_shift_for(user):
    return Shift.objects.filter(user=user, status=Shift.Status.OPEN).first()


class ShiftViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ShiftSerializer

    def get_queryset(self):
        qs = Shift.objects.select_related("user")
        if self.request.user.role != "ADMIN":
            qs = qs.filter(user=self.request.user)
        return qs

    @action(detail=False, methods=["post"])
    def open(self, request):
        """POST /api/shifts/open/  {"initial_cash": "100.00"}"""
        ser = OpenShiftSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            shift = Shift.objects.create(user=request.user, initial_cash=ser.validated_data["initial_cash"])
        except IntegrityError:
            raise ValidationError({"detail": "Ya tienes un turno abierto."})
        return Response(ShiftSerializer(shift).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Turno abierto del usuario autenticado + resumen parcial."""
        shift = _open_shift_for(request.user)
        if not shift:
            return Response({"detail": "No hay turno abierto."}, status=status.HTTP_404_NOT_FOUND)
        return Response({**ShiftSerializer(shift).data, "summary": shift.summary()})

    @action(detail=False, methods=["post"])
    def close(self, request):
        """Cierre de caja: POST /api/shifts/close/ {"final_cash_real": "350.00"}"""
        shift = _open_shift_for(request.user)
        if not shift:
            raise ValidationError({"detail": "No tienes un turno abierto."})
        ser = CloseShiftSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        shift, summary = services.close_shift(
            shift_id=shift.pk, final_cash_real=ser.validated_data["final_cash_real"]
        )
        return Response({**ShiftSerializer(shift).data, "summary": summary})

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        shift = self.get_object()
        return Response({**ShiftSerializer(shift).data, "summary": shift.summary()})


class SaleViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                  mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SaleSerializer

    def get_queryset(self):
        qs = Sale.objects.select_related("user").prefetch_related("items__product")
        if self.request.user.role != "ADMIN":
            qs = qs.filter(user=self.request.user)
        shift = self.request.query_params.get("shift")
        if shift:
            qs = qs.filter(shift_id=shift)
        return qs

    def get_permissions(self):
        if self.action == "void":
            return [IsAdminRole()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        ser = SaleCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        shift = _open_shift_for(request.user)
        if not shift:
            raise ValidationError({"shift": "Debes abrir un turno antes de vender."})
        sale = services.create_sale(
            user=request.user,
            shift=shift,
            payment_method=ser.validated_data["payment_method"],
            items=ser.validated_data["items"],
        )
        sale = self.get_queryset().get(pk=sale.pk)
        return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        """Solo administrador: anula la venta y repone stock."""
        services.void_sale(sale_id=self.get_object().pk)
        return Response(SaleSerializer(self.get_queryset().get(pk=pk)).data)
