#!/usr/bin/env bash
set -Eeuo pipefail

export DEBIAN_FRONTEND=noninteractive

LOG_FILE="/var/log/host-bootstrap-ai.log"

DOCKER_NETWORK_NAME="web_network"

PORTAINER_CONTAINER_NAME="portainer"
PORTAINER_IMAGE="portainer/portainer-ce:lts"
PORTAINER_DATA_VOLUME="portainer_data"
PORTAINER_HTTPS_PORT="9443"
PORTAINER_EDGE_PORT="8000"

OLLAMA_CONTAINER_NAME="ollama"
OLLAMA_IMAGE="ollama/ollama:latest"
OLLAMA_VOLUME="ollama"
OLLAMA_PORT="11434"
OLLAMA_MODEL="deepseek-r1:7b"

retry() {
  local attempts="$1"
  local sleep_seconds="$2"
  shift 2
  local n=1
  until "$@"; do
    if [ "$n" -ge "$attempts" ]; then
      echo "[ERROR] Command failed after ${attempts} attempts: $*" | tee -a "$LOG_FILE"
      return 1
    fi
    echo "[WARN] Attempt ${n}/${attempts} failed: $*" | tee -a "$LOG_FILE"
    n=$((n + 1))
    sleep "$sleep_seconds"
  done
}

require_root() {
  if [ "${EUID}" -ne 0 ]; then
    echo "[ERROR] Run as root" | tee -a "$LOG_FILE"
    exit 1
  fi
}

log() {
  echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"
}

apt_update() {
  retry 5 5 apt-get update
}

install_base_packages() {
  log "Installing base packages"
  apt_update
  retry 5 5 apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    jq \
    pciutils \
    software-properties-common
}

remove_conflicting_docker_packages() {
  log "Removing conflicting Docker packages if present"
  apt-get remove -y docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc || true
}

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    log "Docker already installed"
    return 0
  fi

  log "Installing Docker from Docker apt repository"
  install -m 0755 -d /etc/apt/keyrings
  retry 5 5 curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /tmp/docker.asc
  gpg --dearmor -o /etc/apt/keyrings/docker.gpg /tmp/docker.asc
  chmod a+r /etc/apt/keyrings/docker.gpg

  . /etc/os-release
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list

  apt_update
  retry 5 5 apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin

  systemctl enable docker
  retry 5 5 systemctl restart docker

  retry 10 3 docker version >/dev/null
  retry 10 3 docker info >/dev/null
  log "Docker installed and running"
}

install_nvidia_container_toolkit() {
  if dpkg -s nvidia-container-toolkit >/dev/null 2>&1; then
    log "NVIDIA Container Toolkit already installed"
  else
    log "Installing NVIDIA Container Toolkit"
    apt_update
    retry 5 5 apt-get install -y --no-install-recommends ca-certificates curl gnupg2
    retry 5 5 bash -lc 'curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg'
    retry 5 5 bash -lc 'curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed "s#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g" > /etc/apt/sources.list.d/nvidia-container-toolkit.list'
    apt_update
    retry 5 5 apt-get install -y \
      nvidia-container-toolkit \
      nvidia-container-toolkit-base \
      libnvidia-container-tools \
      libnvidia-container1
  fi

  log "Configuring Docker runtime for NVIDIA Container Toolkit"
  retry 5 5 nvidia-ctk runtime configure --runtime=docker
  retry 5 5 systemctl restart docker
  retry 10 3 docker info >/dev/null
}

check_gpu_host() {
  if command -v nvidia-smi >/dev/null 2>&1; then
    log "Host GPU check via nvidia-smi"
    nvidia-smi | tee -a "$LOG_FILE"
    return 0
  fi

  log "nvidia-smi not found on host. Docker GPU containers may still fail until host NVIDIA driver is installed."
  return 1
}

create_network() {
  if docker network inspect "$DOCKER_NETWORK_NAME" >/dev/null 2>&1; then
    log "Docker network ${DOCKER_NETWORK_NAME} already exists"
    return 0
  fi
  log "Creating Docker network ${DOCKER_NETWORK_NAME}"
  docker network create "$DOCKER_NETWORK_NAME" >/dev/null
}

install_or_update_portainer() {
  log "Installing or updating Portainer CE"
  docker volume create "$PORTAINER_DATA_VOLUME" >/dev/null 2>&1 || true

  if docker ps -a --format '{{.Names}}' | grep -Fxq "$PORTAINER_CONTAINER_NAME"; then
    docker rm -f "$PORTAINER_CONTAINER_NAME" >/dev/null 2>&1 || true
  fi

  retry 5 5 docker pull "$PORTAINER_IMAGE"

  retry 5 5 docker run -d \
    -p "${PORTAINER_EDGE_PORT}:8000" \
    -p "${PORTAINER_HTTPS_PORT}:9443" \
    --name "$PORTAINER_CONTAINER_NAME" \
    --restart=always \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "${PORTAINER_DATA_VOLUME}:/data" \
    "$PORTAINER_IMAGE"

  retry 20 3 docker ps --format '{{.Names}}' | grep -Fxq "$PORTAINER_CONTAINER_NAME"
  log "Portainer is running on https://$(hostname -I | awk '{print $1}'):${PORTAINER_HTTPS_PORT}"
}

install_or_update_ollama_container() {
  log "Installing or updating Ollama container"
  docker volume create "$OLLAMA_VOLUME" >/dev/null 2>&1 || true

  if docker ps -a --format '{{.Names}}' | grep -Fxq "$OLLAMA_CONTAINER_NAME"; then
    docker rm -f "$OLLAMA_CONTAINER_NAME" >/dev/null 2>&1 || true
  fi

  retry 5 5 docker pull "$OLLAMA_IMAGE"

  retry 5 5 docker run -d \
    --gpus=all \
    -v "${OLLAMA_VOLUME}:/root/.ollama" \
    -p "${OLLAMA_PORT}:11434" \
    --name "$OLLAMA_CONTAINER_NAME" \
    --restart=unless-stopped \
    --network "$DOCKER_NETWORK_NAME" \
    "$OLLAMA_IMAGE"

  retry 30 2 bash -lc "curl -fsS http://127.0.0.1:${OLLAMA_PORT}/api/tags >/dev/null"
  log "Ollama API is responding on http://127.0.0.1:${OLLAMA_PORT}"
}

verify_ollama_container() {
  log "Checking Ollama container logs"
  docker logs --tail 100 "$OLLAMA_CONTAINER_NAME" | tee -a "$LOG_FILE" || true

  log "Checking Ollama API tags"
  curl -fsS "http://127.0.0.1:${OLLAMA_PORT}/api/tags" | tee -a "$LOG_FILE"
}

pull_model_in_ollama_container() {
  log "Pulling model inside the Ollama container via docker exec: ${OLLAMA_MODEL}"
  retry 3 10 docker exec "$OLLAMA_CONTAINER_NAME" ollama pull "$OLLAMA_MODEL"
  log "Installed models in Ollama"
  docker exec "$OLLAMA_CONTAINER_NAME" ollama list | tee -a "$LOG_FILE"
}

smoke_test_gpu_container_runtime() {
  log "Running Docker GPU smoke test with Ollama container present"
  if docker inspect "$OLLAMA_CONTAINER_NAME" >/dev/null 2>&1; then
    docker inspect "$OLLAMA_CONTAINER_NAME" --format '{{json .HostConfig.DeviceRequests}}' | tee -a "$LOG_FILE"
  fi
}

maybe_recover_docker_runtime() {
  log "Running Docker runtime recovery steps"
  systemctl daemon-reload || true
  retry 5 5 systemctl restart docker
  sleep 3
}

main() {
  require_root
  mkdir -p "$(dirname "$LOG_FILE")"
  touch "$LOG_FILE"

  log "Starting host bootstrap"
  install_base_packages
  remove_conflicting_docker_packages
  install_docker
  install_nvidia_container_toolkit || {
    log "NVIDIA Container Toolkit setup failed on first attempt, retrying after Docker restart"
    maybe_recover_docker_runtime
    install_nvidia_container_toolkit
  }

  check_gpu_host || true

  create_network
  install_or_update_portainer
  install_or_update_ollama_container || {
    log "Ollama container start failed on first attempt, retrying after Docker restart"
    maybe_recover_docker_runtime
    install_or_update_ollama_container
  }

  smoke_test_gpu_container_runtime
  verify_ollama_container

  pull_model_in_ollama_container || {
    log "Model pull failed on first attempt, restarting Ollama container once and retrying"
    docker restart "$OLLAMA_CONTAINER_NAME"
    retry 30 2 bash -lc "curl -fsS http://127.0.0.1:${OLLAMA_PORT}/api/tags >/dev/null"
    pull_model_in_ollama_container
  }

  log "Bootstrap complete"
  log "Portainer: https://$(hostname -I | awk '{print $1}'):${PORTAINER_HTTPS_PORT}"
  log "Ollama API: http://$(hostname -I | awk '{print $1}'):${OLLAMA_PORT}"
  log "Model installed: ${OLLAMA_MODEL}"
}

main "$@"