#!/bin/bash -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR

source env.sh

# Variables
GITHUB_USERNAME="kinddragon"
GITHUB_REPOSITORY="pre-commit-gn-format"
IMAGE_NAME="ghcr.io/$GITHUB_USERNAME/$GITHUB_REPOSITORY/gn-format-hook"

GIT_REVISION_FULL=$(curl -s "https://chrome-infra-packages.appspot.com/p/gn/gn/linux-amd64/+/latest" | grep -o 'git_revision:[a-f0-9]\{40\}' | head -1 | cut -d ':' -f 2)
# -A 1 to include next line, sed -n 2p to pick second line, next sed to extract ID
INSTANCE_ID=$(curl -s "https://chrome-infra-packages.appspot.com/p/gn/gn/linux-amd64/+/latest" | grep -A 1 "Instance ID" | sed -n 2p | sed 's/.*>\(.*\)<.*/\1/')

if [ -z "$GIT_REVISION_FULL" ] || [ -z "$INSTANCE_ID" ]; then
    echo "Failed to fetch the latest GN version details."
    exit 1
fi

# Extract the first 12 characters of the git_revision
GIT_REVISION=${GIT_REVISION_FULL:0:12}

# Check if the latest git_revision is different from the current git tag
CURRENT_GIT_REVISION=$(git tag --list "$GIT_REVISION")
if [ "$GIT_REVISION" = "$CURRENT_GIT_REVISION" ]; then
    echo "GN version is already up-to-date with git revision $GIT_REVISION."
    exit 0
fi

# Patch the Dockerfile and .pre-commit-hooks.yaml with the instance_id and git_revision respectively
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/INSTANCE_ID=\"[^\"]*\"/INSTANCE_ID=\"$INSTANCE_ID\"/" Dockerfile
    sed -i '' "s|$IMAGE_NAME:[^\"]*|$IMAGE_NAME:$GIT_REVISION|" .pre-commit-hooks.yaml
else
    sed -i "s/INSTANCE_ID=\"[^\"]*\"/INSTANCE_ID=\"$INSTANCE_ID\"/" Dockerfile
    sed -i "s|$IMAGE_NAME:[^\"]*|$IMAGE_NAME:$GIT_REVISION|" .pre-commit-hooks.yaml
fi

git add Dockerfile .pre-commit-hooks.yaml
git commit -m "Update GN Format hook to GN git revision $GIT_REVISION" || {
    echo "No changes detected in Dockerfile or .pre-commit-hooks.yaml."
    read -p "Do you want to continue? [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            echo "Continuing with the process..."
            ;;
        *)
            echo "Process aborted."
            exit 0
            ;;
    esac
}

docker build -t $IMAGE_NAME .

# Tag the Image with 'latest'
docker tag $IMAGE_NAME $IMAGE_NAME:latest

# Tag the Image with 'GIT_REVISION'
docker tag $IMAGE_NAME $IMAGE_NAME:$GIT_REVISION

# Log in to GitHub Packages
echo $GITHUB_PAT | docker login ghcr.io -u $GITHUB_USERNAME --password-stdin

# Push the 'latest' tag
docker push $IMAGE_NAME:latest

# Push the 'GIT_REVISION' tag
docker push $IMAGE_NAME:$GIT_REVISION

# Create a local git tag with GIT_REVISION
git tag -a "$GIT_REVISION" -m "GN git revision $GIT_REVISION"
git push origin "$GIT_REVISION"
