

from rest_framework import serializers

class CompileCCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=5000)
