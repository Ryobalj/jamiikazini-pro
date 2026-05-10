# businesses/serializers/branch_serializer.py

from rest_framework import serializers
from businesses.models.branch import Branch


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = [
            'id',
            'business',
            'name',
            'description',
            'location',
            'phone',
            'email',
            'is_active',
            'services',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'business': {'help_text': "Biashara inayomiliki tawi hili."},
            'name': {'help_text': "Jina la tawi (mfano: Tawi la Mlimani City)."},
            'description': {'help_text': "Maelezo mafupi kuhusu tawi hili."},
            'location': {'help_text': "Mahali lilipo tawi (PointField - lat/lng)."},
            'phone': {'help_text': "Namba ya simu ya mawasiliano ya tawi."},
            'email': {'help_text': "Barua pepe ya mawasiliano ya tawi."},
            'is_active': {'help_text': "Je, tawi hili linafanya kazi kwa sasa?"},
            'services': {'help_text': "Huduma zinazopatikana kwenye tawi hili (ManyToMany)."},
        }

    def create(self, validated_data):
        services = validated_data.pop("services", [])
        branch = Branch.objects.create(**validated_data)
        if services:
            branch.services.set(services)
        return branch

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["business_name"] = instance.business.name
        rep["services_count"] = instance.services.count()
        return rep