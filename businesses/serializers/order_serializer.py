from decimal import Decimal
from django.contrib.gis.geos import Point
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from businesses.models.order import Order, OrderItem, PaymentStatus, FulfillmentType, PaymentTerms, PaymentMethod
from businesses.models.product import Product, WHOLE_UNIT_TYPES
from businesses.models.product_offer import ProductOffer, ProductOfferStatus
from businesses.models.service import Service
from jamiiwallet.models.transaction import Transaction as WalletTransaction
from jamiiwallet.services.transaction_engine import TransactionEngine


class DeliverySerializer(serializers.Serializer):
    """Maelezo ya usafiri - yanahitajika tu wakati fulfillment_type=DELIVERY."""
    vehicle_type = serializers.CharField()
    dropoff_lat = serializers.FloatField()
    dropoff_lng = serializers.FloatField()
    dropoff_address_text = serializers.CharField(required=False, allow_blank=True, default="")
    weight_kg = serializers.FloatField(required=False, default=5.0)
    volume_cbm = serializers.FloatField(required=False, allow_null=True, default=None)


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False)
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all(), required=False)
    product_name = serializers.CharField(source="product.name", read_only=True, default=None)
    service_name = serializers.CharField(source="service.name", read_only=True, default=None)
    unit = serializers.CharField(source="product.unit", read_only=True, default=None)
    # offer si field halisi ya OrderItem - inatolewa kwenye validated_data ili
    # itumike kupata bei iliyokubaliwa (angalia validate()), kisha inaondolewa
    # (pop) kabla ya OrderItem.objects.create() kwenye OrderSerializer.create().
    offer = serializers.PrimaryKeyRelatedField(queryset=ProductOffer.objects.all(), required=False, write_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "service", "product_name", "service_name", "unit", "quantity", "unit_price", "total_price", "order", "offer"]
        # unit_price ni SERVER-COMPUTED kutoka bei halisi ya Product/Service ya sasa -
        # kamwe usiitegemee thamani ya mteja, la sivyo mteja anaweza kutuma bei yoyote
        # anayotaka kwenye ombi (mf. TZS 1 badala ya bei halisi).
        read_only_fields = ["id", "unit_price", "total_price", "order"]

    def validate(self, attrs):
        product = attrs.get("product")
        service = attrs.get("service")
        if not product and not service:
            raise serializers.ValidationError("Lazima uchague Product au Service.")
        if product and service:
            raise serializers.ValidationError("Chagua Product AU Service, si vyote viwili.")

        quantity = attrs.get("quantity", 1)
        offer = attrs.get("offer")
        if offer is not None:
            request = self.context.get("request")
            user = getattr(request, "user", None)
            if user is None or offer.buyer_id != user.id:
                raise serializers.ValidationError({"offer": "Ofa hii si yako."})
            if offer.product_id != (product.id if product else None):
                raise serializers.ValidationError({"offer": "Ofa hii si ya bidhaa hii."})
            if offer.status != ProductOfferStatus.ACCEPTED:
                raise serializers.ValidationError({"offer": "Ofa hii bado haijakubaliwa au tayari imekataliwa."})
            if offer.consumed:
                raise serializers.ValidationError({"offer": "Ofa hii tayari imetumika kwenye oda nyingine."})
            if offer.quantity != quantity:
                raise serializers.ValidationError({"offer": f"Kiasi lazima kiwe sawa na ulichoomba kwenye ofa ({offer.quantity})."})

        if product:
            if not product.is_available:
                raise serializers.ValidationError(f"'{product.name}' haipatikani kwa sasa.")
            if product.unit in WHOLE_UNIT_TYPES and quantity % 1 != 0:
                raise serializers.ValidationError(
                    f"'{product.name}' inauzwa kwa idadi kamili tu ({product.get_unit_display()}), si desimali."
                )
            if product.quantity_in_stock < quantity:
                raise serializers.ValidationError(
                    f"Stock haitoshi kwa '{product.name}' (zilizopo: {product.quantity_in_stock})."
                )
            if offer is not None:
                # Bei iliyojadiliwa na kukubaliwa - inashinda price_for_quantity/wholesale tier.
                attrs["unit_price"] = offer.accepted_unit_price
                return attrs
            # Bei ya jumla (wholesale tier) kama kiasi kinachonunuliwa kinakidhi
            # MOQ ya tier - wazi kwa mnunuzi yeyote, si tu ununuzi wa B2B.
            attrs["unit_price"] = product.price_for_quantity(quantity)
        else:
            if quantity % 1 != 0:
                raise serializers.ValidationError("Huduma zinunuliwa kwa idadi kamili tu, si desimali.")
            attrs["unit_price"] = service.price

        return attrs


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    delivery = DeliverySerializer(write_only=True, required=False)
    business_name = serializers.CharField(source="business.name", read_only=True, default=None)
    can_mark_cash_received = serializers.SerializerMethodField()
    referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    def get_can_mark_cash_received(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None:
            return False
        return (
            obj.payment_method == PaymentMethod.CASH
            and obj.payment_status == PaymentStatus.CASH_PENDING
            and (user.is_superuser or obj.business.owner_id == user.id)
        )

    class Meta:
        model = Order
        fields = [
            "id",
            "client",
            "business",
            "business_name",
            "status",
            "payment_status",
            "fulfillment_type",
            "payment_method",
            "can_mark_cash_received",
            "delivery_fee",
            "scheduled_datetime",
            "notes",
            "total_amount",
            "items",
            "delivery",
            "purchasing_business",
            "payment_terms",
            "invoice",
            "referral_code",
            "created_at",
            "updated_at",
        ]
        # payment_status/delivery_fee ni server-controlled - huwekwa kulingana
        # na matokeo ya malipo/HOLD (angalia create()). status unabaki writable
        # kwa sababu muuzaji anahitaji kuubadilisha (PENDING -> PROCESSING ->
        # COMPLETED) kupitia update. purchasing_business/payment_terms/payment_method
        # ni writable - mnunuzi anaziweka wakati wa checkout (angalia validate()
        # kwa ukaguzi wa umiliki na masharti ya CASH).
        read_only_fields = ["id", "client", "payment_status", "can_mark_cash_received", "delivery_fee", "total_amount", "invoice", "created_at", "updated_at"]

    def validate(self, attrs):
        # Items ni lazima wakati wa CREATE tu; partial update (mf. notes) isidai items
        if self.instance is None:
            if attrs.get("fulfillment_type") == FulfillmentType.DELIVERY and not attrs.get("delivery"):
                raise serializers.ValidationError(
                    {"delivery": "Maelezo ya usafiri yanahitajika kwa fulfillment_type=DELIVERY."}
                )

            items = self.initial_data.get("items", [])
            if not items:
                raise serializers.ValidationError("Order lazima iwe na angalau item moja.")

            purchasing_business = attrs.get("purchasing_business")
            payment_terms = attrs.get("payment_terms", PaymentTerms.IMMEDIATE)
            if payment_terms != PaymentTerms.IMMEDIATE and not purchasing_business:
                raise serializers.ValidationError(
                    {"payment_terms": "Masharti ya mkopo yanapatikana tu unaponunua kama biashara."}
                )
            if purchasing_business is not None:
                request = self.context.get("request")
                user = getattr(request, "user", None)
                if user is None or purchasing_business.owner_id != user.id:
                    raise serializers.ValidationError(
                        {"purchasing_business": "Huwezi kununua kama biashara isiyo yako."}
                    )
                if not purchasing_business.is_verified:
                    raise serializers.ValidationError(
                        {"purchasing_business": "Biashara hii bado haijathibitishwa - huwezi kununua kwa jina lake."}
                    )
                if attrs.get("fulfillment_type") == FulfillmentType.DELIVERY and payment_terms != PaymentTerms.IMMEDIATE:
                    raise serializers.ValidationError(
                        {"payment_terms": "Masharti ya mkopo yanapatikana tu kwa PICKUP kwa sasa."}
                    )

            payment_method = attrs.get("payment_method", PaymentMethod.WALLET)
            if payment_method == PaymentMethod.CASH:
                # Mirrors the DELIVERY-check polarity used elsewhere in this method -
                # fulfillment_type defaults to PICKUP at the model level and is only
                # present in attrs when the client explicitly submits it, so a missing
                # key must be treated as PICKUP (allowed), not rejected.
                if attrs.get("fulfillment_type") == FulfillmentType.DELIVERY:
                    raise serializers.ValidationError(
                        {"payment_method": "Malipo taslimu yanapatikana tu kwa PICKUP."}
                    )
                if payment_terms != PaymentTerms.IMMEDIATE:
                    raise serializers.ValidationError(
                        {"payment_method": "Malipo taslimu hayawezi kuchanganywa na masharti ya mkopo."}
                    )
                sale_business = attrs.get("business")
                if not sale_business or not sale_business.is_verified:
                    raise serializers.ValidationError(
                        {"payment_method": "Malipo taslimu yanapatikana tu kwa biashara zilizothibitishwa."}
                    )

            business = attrs.get("business")
            if business:
                for item in self.initial_data.get("items", []):
                    product_id = item.get("product")
                    service_id = item.get("service")
                    if product_id and not Product.objects.filter(id=product_id, business_id=business.id).exists():
                        raise serializers.ValidationError("Bidhaa moja au zaidi hazitoki kwenye biashara hii.")
                    if service_id and not Service.objects.filter(id=service_id, business_id=business.id).exists():
                        raise serializers.ValidationError("Huduma moja au zaidi hazitoki kwenye biashara hii.")
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop("items")
        delivery_data = validated_data.pop("delivery", None)
        referral_code = validated_data.pop("referral_code", None)
        if referral_code:
            from kiini.models.referral_code import ReferralCode
            referral = ReferralCode.objects.filter(code=referral_code.strip().upper()).select_related("user").first()
            buyer = validated_data.get("client")
            # Silently ignore an invalid code or self-referral - no error, just no dalali credited.
            if referral and buyer is not None and referral.user_id != buyer.id:
                validated_data["referred_by"] = referral.user
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            offer = item_data.pop("offer", None)
            product = item_data.get("product")
            if product:
                # select_for_update kuzuia mbio ya order mbili zinazomaliza stock ile ile.
                # Punguzo halisi la quantity_in_stock hufanywa na
                # businesses.signals.decrement_stock_on_order_item_created (post_save ya
                # OrderItem) - hapa tunafanya tu ukaguzi wa awali ndani ya lock ile ile,
                # bila kupunguza wenyewe, ili isipunguzwe mara mbili.
                locked_product = Product.objects.select_for_update().get(pk=product.pk)
                if locked_product.quantity_in_stock < item_data["quantity"]:
                    raise serializers.ValidationError(
                        f"Stock haitoshi kwa '{locked_product.name}' (zilizopo: {locked_product.quantity_in_stock})."
                    )
            OrderItem.objects.create(order=order, **item_data)
            if offer is not None:
                offer.consumed = True
                offer.save(update_fields=["consumed"])

        # Recalculate total
        order.total_amount = order.calculate_total()
        order.save(update_fields=["total_amount"])

        if order.business.owner_id:
            from kiini.helpers.notification_helper import notify_user
            from kiini.models.notification import NotificationType
            notify_user(
                order.business.owner,
                f"Umepata oda mpya kutoka kwa {order.client.full_name if order.client else 'mteja'}.",
                notification_type=NotificationType.ORDER,
                link=f"/orders/{order.id}",
            )

        if order.payment_terms != PaymentTerms.IMMEDIATE:
            # B2B credit order (validate() already confirmed PICKUP + business
            # ownership) - hakuna kuguswa kwa wallet hapa kabisa, invoice
            # inaundwa badala yake na kulipwa baadaye (angalia
            # payments/views/invoice_views.py::pay).
            self._create_credit_order(order)
            return order

        if order.payment_method == PaymentMethod.CASH:
            # validate() already confirmed PICKUP + business.is_verified +
            # payment_terms=IMMEDIATE. Neither party's wallet is touched at
            # all - the buyer pays physically at pickup, and the business
            # owner marks it received via OrderViewSet.mark_cash_received.
            order.payment_status = PaymentStatus.CASH_PENDING
            order.save(update_fields=["payment_status"])
            return order

        client_wallet = getattr(order.client, "wallet", None)
        merchant_wallet = getattr(order.business.owner, "wallet", None)
        if not client_wallet or not merchant_wallet:
            raise serializers.ValidationError(
                {"payment": "Wallet haipatikani kwa mmoja wa wahusika - lipia haiwezekani."}
            )

        if order.fulfillment_type == FulfillmentType.PICKUP:
            # Malipo ya bidhaa/huduma hufanyika kupitia JamiiWallet PEKEE - njia
            # nyingine za malipo (kadi, simu n.k.) ni kwa ajili ya kuweka/kutoa
            # pesa kwenye wallet, si kwa manunuzi ya moja kwa moja. Ikiwa malipo
            # hayajafanikiwa, order nzima (na upunguzaji wa stock) hurudishwa nyuma
            # kwa sababu tuko ndani ya @transaction.atomic.
            payment_txn = TransactionEngine.initiate(
                wallet=client_wallet,
                amount=order.total_amount,
                transaction_type=WalletTransaction.TransactionType.PAYMENT,
                initiated_by=order.client,
                counterparty=order.business.owner,
                metadata={"order_id": str(order.id)},
            )
            try:
                TransactionEngine.process(payment_txn)
            except DjangoValidationError:
                raise serializers.ValidationError(
                    {"payment": "Salio la JamiiWallet halitoshi kulipia order hii."}
                )

            order.payment_status = PaymentStatus.PAID
            order.save(update_fields=["payment_status"])
            self._pay_broker_commission(order)
        else:
            self._create_delivery(order, delivery_data, client_wallet)

        return order

    @staticmethod
    def _pay_broker_commission(order):
        """
        Kamisheni ya dalali (v1: PICKUP + wallet PAID pekee - DELIVERY/mkopo/
        taslimu hazijajumuishwa kwa sasa). Inatumia Transfer (jamiiwallet) ile
        ile inayotumika na cash-out - hakuna injini mpya ya malipo. Hitilafu
        yoyote hapa haipaswi kufuta oda iliyokwisha lipwa, hivyo imezungukwa
        na try/except badala ya kuiacha ivunje transaction nzima.
        """
        if not order.referred_by_id or not order.business.broker_commission_rate:
            return
        if order.referred_by_id == order.business.owner_id:
            return
        try:
            from jamiiwallet.models.transfer import Transfer
            commission = (order.total_amount * order.business.broker_commission_rate / Decimal("100")).quantize(Decimal("0.01"))
            if commission <= 0:
                return
            Transfer.objects.create(
                sender=order.business.owner,
                recipient=order.referred_by,
                amount=commission,
                note=f"Kamisheni ya dalali - Order {order.id}",
            )
        except Exception:
            pass

    @staticmethod
    def _create_credit_order(order):
        """
        B2B order kwa masharti ya mkopo (NET_15/NET_30) - badala ya kushikilia
        (HOLD) fedha za wallet mara moja, tunaunda Invoice (payments app,
        model iliyopo tayari - hakuna mfano mpya) na kuongeza outstanding_credit
        ya BusinessCreditAccount ya purchasing_business. Mnunuzi analipa baadaye
        kupitia payments/views/invoice_views.py::InvoiceViewSet.pay (siyo
        mark-paid ya admin, ambayo haihamishi fedha).
        """
        from datetime import timedelta
        from django.utils import timezone
        from businesses.models.business_credit_account import BusinessCreditAccount
        from payments.models.invoice import Invoice

        try:
            credit_account = BusinessCreditAccount.objects.select_for_update().get(
                business=order.purchasing_business
            )
        except BusinessCreditAccount.DoesNotExist:
            raise serializers.ValidationError(
                {"payment_terms": "Biashara hii haina akaunti ya mkopo iliyoidhinishwa."}
            )

        if credit_account.outstanding_credit + order.total_amount > credit_account.credit_limit:
            raise serializers.ValidationError(
                {"payment_terms": "Kikomo cha mkopo hakitoshi kwa oda hii."}
            )

        days = 15 if order.payment_terms == PaymentTerms.NET_15 else 30
        invoice = Invoice.objects.create(
            invoice_number=f"INV-{order.id.hex[:12].upper()}",
            user=order.purchasing_business.owner,
            amount=order.total_amount,
            tax=Decimal("0.00"),
            due_date=(timezone.now() + timedelta(days=days)).date(),
            created_by=order.client,
            description=f"B2B order {order.id} kutoka {order.business.name}",
        )
        order.invoice = invoice
        order.save(update_fields=["invoice"])

        credit_account.outstanding_credit += order.total_amount
        credit_account.save(update_fields=["outstanding_credit"])

    def _create_delivery(self, order, delivery_data, client_wallet):
        """
        Kwa fulfillment_type=DELIVERY: kadiria bei ya usafiri, shikilia (HOLD)
        jumla (bidhaa + usafiri) kwenye wallet ya mnunuzi (badala ya kulipa moja
        kwa moja), kisha unda TransportRequest itakayotangazwa kwa madereva wa
        karibu. Fedha zitaachiliwa tu baada ya dereva kuthibitisha kufikisha NA
        mnunuzi kuthibitisha kupokea (angalia logistics/services/escrow_release.py).
        """
        from logistics.models.rate_card import TransportRateCard
        from logistics.models.transport_request import TransportRequest
        from logistics.choices import TransportRequestStatus
        from logistics.services.weight_bands import is_vehicle_suitable

        vehicle_type = delivery_data["vehicle_type"]
        try:
            rate_card = TransportRateCard.objects.get(vehicle_type=vehicle_type, is_active=True)
        except TransportRateCard.DoesNotExist:
            raise serializers.ValidationError({"delivery": "Aina hii ya usafiri haipatikani kwa sasa."})

        business_location = order.business.location
        if not business_location:
            raise serializers.ValidationError({"delivery": "Biashara hii haijaweka eneo lake - usafiri hauwezekani."})

        dropoff_point = Point(delivery_data["dropoff_lng"], delivery_data["dropoff_lat"], srid=4326)
        distance_km = business_location.distance(dropoff_point) * 100  # deg -> approx km, sawa na TransportRequest.calculate_distance_km()

        weight_kg = delivery_data.get("weight_kg") or 5.0
        volume_cbm = delivery_data.get("volume_cbm")
        if not is_vehicle_suitable(vehicle_type, weight_kg, distance_km, volume_cbm):
            raise serializers.ValidationError({"delivery": "Aina hii ya usafiri haifai kwa uzito/umbali wa mzigo huu."})

        delivery_fee = rate_card.estimate_fare(distance_km, weight_kg)
        order.delivery_fee = delivery_fee
        order.total_amount = order.calculate_total()
        order.save(update_fields=["delivery_fee", "total_amount"])

        hold_txn = TransactionEngine.initiate(
            wallet=client_wallet,
            amount=order.total_amount,
            transaction_type=WalletTransaction.TransactionType.HOLD,
            initiated_by=order.client,
            metadata={"order_id": str(order.id)},
        )
        try:
            TransactionEngine.process(hold_txn)
        except DjangoValidationError:
            raise serializers.ValidationError(
                {"payment": "Salio la JamiiWallet halitoshi kulipia bidhaa na usafiri kwa pamoja."}
            )

        order.payment_status = PaymentStatus.HELD
        order.save(update_fields=["payment_status"])

        new_transport_request = TransportRequest.objects.create(
            requestor_type="business",
            business=order.business,
            order=order,
            package_description=order.notes or f"Order {order.id}",
            weight_kg=weight_kg,
            volume_cbm=volume_cbm,
            estimated_value=order.total_amount - order.delivery_fee,
            suggested_transport_type=vehicle_type,
            pickup_location=business_location,
            dropoff_location=dropoff_point,
            pickup_address_text=order.business.address or "",
            dropoff_address_text=delivery_data.get("dropoff_address_text") or "",
            status=TransportRequestStatus.PENDING,
            estimated_fare=delivery_fee,
        )
        self._notify_nearby_drivers(new_transport_request, vehicle_type)

    @staticmethod
    def _notify_nearby_drivers(transport_request, vehicle_type, max_distance_km=50):
        from django.contrib.gis.db.models.functions import Distance as GisDistance
        from logistics.models.vehicle import Vehicle
        from kiini.helpers.notification_helper import notify_user

        vehicles = Vehicle.objects.filter(
            vehicle_type=vehicle_type,
            is_active=True,
            active_driver__isnull=False,
            provider__location__isnull=False,
        ).annotate(
            distance=GisDistance("provider__location", transport_request.pickup_location)
        ).filter(distance__lte=max_distance_km * 1000).select_related("provider__user")

        notified_users = set()
        for vehicle in vehicles:
            user = vehicle.provider.user
            if user.id in notified_users:
                continue
            notified_users.add(user.id)
            notify_user(user, "Kuna ombi jipya la usafiri karibu nawe kwenye Jamiikazini.")

    @transaction.atomic
    def update(self, instance, validated_data):
        # items ni hiari kwenye partial update - usifute items zilizopo bila mpya
        items_data = validated_data.pop("items", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is None:
            return instance

        # Delete old items and recreate
        instance.items.all().delete()
        for item_data in items_data:
            item_data.pop("offer", None)
            OrderItem.objects.create(order=instance, **item_data)

        instance.total_amount = instance.calculate_total()
        instance.save(update_fields=["total_amount"])
        return instance
