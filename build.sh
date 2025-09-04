#!/bin/bash

echo "🚀 NEXIUN - Build Script"
echo "=========================="

# Nome da imagem
IMAGE_NAME="nexiun"
TAG="latest"

echo "📦 Construindo imagem Docker: $IMAGE_NAME:$TAG"

# Build da imagem usando o Dockerfile na pasta deploy
docker build -f deploy/Dockerfile -t $IMAGE_NAME:$TAG .

if [ $? -eq 0 ]; then
    echo "✅ Imagem construída com sucesso!"
    echo ""
    echo "🐳 Para testar localmente:"
    echo "docker run -p 8000:8000 --env-file .env $IMAGE_NAME:$TAG"
    echo ""
    echo "🏷️ Para fazer tag para deploy:"
    echo "docker tag $IMAGE_NAME:$TAG easypanel/nexiun/django:$TAG"
else
    echo "❌ Erro na construção da imagem!"
    exit 1
fi 