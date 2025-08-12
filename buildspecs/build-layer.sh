#!/bin/bash
# filepath: build-layer.sh

set -e

LAYER_NAME="tracker-stack-dependencies"
LAYER_DIR="layer-build"
PYTHON_VERSION="python3.11"

echo "Building Lambda layer: $LAYER_NAME"

# Clean up previous builds
rm -rf $LAYER_DIR
mkdir -p $LAYER_DIR/python

# Install dependencies to the layer directory
echo "Installing dependencies..."
pip install -r ../requirements.txt -t $LAYER_DIR/python/

# Create layer zip
echo "Creating layer package..."
cd $LAYER_DIR
zip -r ../${LAYER_NAME}.zip .
cd ..

# Upload layer to AWS
echo "Publishing layer to AWS..."
LAYER_VERSION=$(aws lambda publish-layer-version \
    --layer-name $LAYER_NAME \
    --description "Dependencies for tracker stack Lambda functions" \
    --zip-file fileb://${LAYER_NAME}.zip \
    --compatible-runtimes $PYTHON_VERSION \
    --query 'Version' \
    --output text)

echo "Layer published successfully!"
echo "Layer Name: $LAYER_NAME"
echo "Layer Version: $LAYER_VERSION"
echo "Layer ARN: arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:layer:${LAYER_NAME}:${LAYER_VERSION}"

# Clean up
rm -rf $LAYER_DIR ${LAYER_NAME}.zip

echo "Layer build completed!"