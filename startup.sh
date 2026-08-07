#!/bin/bash
set -e

echo "Compiling Qt resources..."
uv run pyside6-rcc resources.qrc -o resources_rc.py

echo "Copying resources to workspace..."
WORKSPACE_ROOT="${LOCALAPPDATA}/ai-video-gui"
WORKSPACE_RESOURCES="${WORKSPACE_ROOT}/resources"
PROJECT_RESOURCES="./resources"

mkdir -p "${WORKSPACE_RESOURCES}"

for subdir in styles covers; do
    SRC_DIR="${PROJECT_RESOURCES}/${subdir}"
    DST_DIR="${WORKSPACE_RESOURCES}/${subdir}"

    if [ ! -d "${SRC_DIR}" ]; then
        echo "Skipping non-existent directory: ${SRC_DIR}"
        continue
    fi

    mkdir -p "${DST_DIR}"

    for file in "${SRC_DIR}"/*; do
        if [ -f "${file}" ]; then
            filename=$(basename "${file}")
            dst_file="${DST_DIR}/${filename}"

            if [ -f "${dst_file}" ]; then
                if [ "${file}" -nt "${dst_file}" ]; then
                    echo "Updating: ${filename}"
                    cp -p "${file}" "${dst_file}"
                fi
            else
                echo "Copying: ${filename}"
                cp -p "${file}" "${dst_file}"
            fi
        fi
    done
done

echo "Resources synced to: ${WORKSPACE_RESOURCES}"

echo "Starting application..."
uv run main.py
