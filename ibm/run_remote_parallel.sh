#!/usr/bin/env bash
#
# run_remote_parallel.sh
#
# Run many jobs (from your run_all.sh template) in parallel on a REMOTE Docker host,
# collect /app/artifacts back to your local machine, save logs, and clean everything.
#
# REQUIREMENTS:
#   - You have a built/pushed image (e.g., yourname/myproj:<tag>)
#   - You can talk to the remote Docker daemon, e.g.:
#       export DOCKER_HOST="ssh://me@remote-host"
#   - You’re logged in to Docker Hub if the image is private.
#
# QUICK START:
#   export DOCKER_HOST="ssh://me@remote"
#   export IMAGE="yourname/myproj:latest"
#   ./run_remote_parallel.sh
#
# CUSTOMIZATION (env vars):
#   IMAGE=yourname/myproj:latest     # image:tag to run remotely
#   OUT_DIR=./artifacts_remote_runs  # local folder for collected artifacts & logs
#   PARALLEL_LIMIT=0                 # 0=unlimited, or set N to throttle
#   CLEAN_IMAGE=true                 # remove the image from remote afterwards
#   SAVE_LOGS=true                   # save docker logs for each job
#   DOCKER_RUN_EXTRA="--gpus all"    # extra flags for docker run (GPU, envs, etc.)
#
set -euo pipefail

# --------- REQUIRED: remote docker host ----------
: "${DOCKER_HOST:?Set DOCKER_HOST, e.g. 'export DOCKER_HOST=ssh://me@remote-host'}"

# --------- CONFIG (override by exporting env vars) ----------
IMAGE="${IMAGE:-amir/charge-qkd:latest}"
OUT_DIR="${OUT_DIR:-./artifacts}"
PARALLEL_LIMIT="${PARALLEL_LIMIT:-0}"     # 0 = unlimited
CLEAN_IMAGE="${CLEAN_IMAGE:-true}"
SAVE_LOGS="${SAVE_LOGS:-true}"
DOCKER_RUN_EXTRA="${DOCKER_RUN_EXTRA:-}"  # e.g. "--gpus all -e FOO=1"
# -----------------------------------------------------------

# Split DOCKER_RUN_EXTRA into an array safely (if set)
read -r -a RUN_EXTRA_ARR <<< "${DOCKER_RUN_EXTRA:-}"

# Utilities
die() { echo "ERROR: $*" >&2; exit 1; }
timestamp() { date +%Y-%m-%dT%H:%M:%S%z; }

sanitize() {
  # filesystem/container-name safe: lowercase, [a-z0-9-]
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+|-+$//g'
}

running_count() {
  docker ps --filter "label=job_group=${RUN_ID}" --format '{{.ID}}' | wc -l | xargs
}

throttle() {
  local limit="$1"
  [[ "$limit" -le 0 ]] && return 0
  while :; do
    local n; n="$(running_count)"
    [[ "$n" -lt "$limit" ]] && break
    sleep 1
  done
}

# --------- TASK GENERATOR (mirrors your run_all.sh) ----------
# You can edit below to change the job set. Every generated entry becomes one container.
declare -a TASKS # each item: "JobName|main.py <args...>"

gen_tasks_from_template() {
  local -a errors=("bit-flip-errors" "alice-phase-flip-errors" "bob-phase-flip-errors" "excited-mixture-errors" "excited-superposition-errors")
  local -a Ns=(1 2 3)

  # shots per N (matching your script)
  declare -A nn_shots
  nn_shots[1]="10000 10000"
  nn_shots[2]="500000 500000"
  nn_shots[3]="5000000 500000"

  for N in "${Ns[@]}"; do
    # Base (Alice) job
    TASKS+=("N${N}|main.py --both-alice-values -Js 100 -N ${N} -o N${N} -s Alice --alice-base X")

    # NearestNeighbors variants for N>1
    if [[ $N -gt 1 ]]; then
      IFS=' ' read -r shotsX shotsY <<< "${nn_shots[$N]}"
      TASKS+=("N${N}_X|main.py --both-alice-values --shots ${shotsX} -Js 100 -N ${N} -o N${N}_X -s NearestNeighbors --alice-base X")
      TASKS+=("N${N}_Y|main.py --both-alice-values --shots ${shotsX} -Js 100 -N ${N} -o N${N}_Y -s NearestNeighbors --alice-base Y")
    fi

    # Error sweeps
    for err in "${errors[@]}"; do
      dir="N${N}-${err}"
      TASKS+=("${dir}|main.py --avoid-J0 -Js 8 -N ${N} --${err} -o ${dir} -s Alice --alice-base X")
      if [[ $N -gt 1 ]]; then
        IFS=' ' read -r shotsX shotsY <<< "${nn_shots[$N]}"
        TASKS+=("${dir}_X|main.py --shots ${shotsX} --avoid-J0 -Js 8 -N ${N} --${err} -o ${dir}_X -s NearestNeighbors --alice-base X")
        TASKS+=("${dir}_Y|main.py --shots ${shotsY} --avoid-J0 -Js 8 -N ${N} --${err} -o ${dir}_Y -s NearestNeighbors --alice-base Y")
      fi
    done
  done
}

# Generate tasks now
gen_tasks_from_template

# --------- PREP ---------
mkdir -p "$OUT_DIR"
RUN_ID="run-$(date +%Y%m%d-%H%M%S)-$RANDOM"
echo "[$(timestamp)] Remote host: $DOCKER_HOST"
echo "[$(timestamp)] Image:       $IMAGE"
echo "[$(timestamp)] Run ID:      $RUN_ID"
echo "[$(timestamp)] Tasks:       ${#TASKS[@]}"
echo

# Pull image on remote if missing
docker image inspect "$IMAGE" >/dev/null 2>&1 || docker pull "$IMAGE" >/dev/null

# Trap to force-kill & remove on error/interrupt (best-effort)
cleanup_trap() {
  echo
  echo "[$(timestamp)] Trap: cleaning any leftover containers for ${RUN_ID}..."
  # Stop quickly (if any still running), then remove with volumes
  ids="$(docker ps -aq --filter "label=job_group=${RUN_ID}")" || true
  if [[ -n "${ids:-}" ]]; then
    docker rm -fv $ids >/dev/null 2>&1 || true
  fi
  if [[ "${CLEAN_IMAGE}" == "true" ]]; then
    docker rmi "$IMAGE" >/dev/null 2>&1 || true
  fi
}
trap cleanup_trap EXIT INT TERM

# --------- LAUNCH ALL JOBS (detached) ---------
declare -a CONTAINERS=()
declare -A JOB2NAME=()

for entry in "${TASKS[@]}"; do
  IFS='|' read -r job cmd <<< "$entry"
  safe_job="$(sanitize "$job")"
  cname="${RUN_ID}-${safe_job}"

  # throttle concurrency if requested
  throttle "$PARALLEL_LIMIT"

  echo "[$(timestamp)] Start: ${job}  -> container ${cname}"

  # We override entrypoint so we can keep your "echo | python ..." behavior.
  # Working dir is /app (from Dockerfile). PATH already includes venv bin.
  # We also ensure /app/artifacts exists (harmless if already there).
  docker run -d \
    --name "$cname" \
    --label "job_group=${RUN_ID}" \
    "${RUN_EXTRA_ARR[@]}" \
    --entrypoint /bin/sh \
    "$IMAGE" \
    -lc "mkdir -p /app/artifacts && echo | python ${cmd}" >/dev/null

  CONTAINERS+=("$cname")
  JOB2NAME["$cname"]="$job"
done

echo
echo "[$(timestamp)] Waiting for jobs to finish..."
declare -A EXITCODES=()

for cname in "${CONTAINERS[@]}"; do
  code="$(docker wait "$cname")" || code="$?"
  EXITCODES["$cname"]="$code"
  echo "[$(timestamp)] Done: ${JOB2NAME[$cname]} -> exit $code"
done

# --------- COLLECT ARTIFACTS & LOGS ---------
echo
echo "[$(timestamp)] Collecting artifacts into: $OUT_DIR"
for cname in "${CONTAINERS[@]}"; do
  job="${JOB2NAME[$cname]}"
  dest="${OUT_DIR}/$(sanitize "$job")"
  mkdir -p "$dest"

  # Copy artifacts (contents) from container
  if docker cp "${cname}:/app/artifacts/." "$dest/" 2>/dev/null; then
    :
  else
    echo "  (no artifacts for ${job})"
  fi

  # Save logs for debugging / provenance
  if [[ "${SAVE_LOGS}" == "true" ]]; then
    docker logs "$cname" > "${dest}/container.log" 2>&1 || true
  fi
done

# --------- CLEANUP REMOTE (containers, volumes, image) ---------
echo
echo "[$(timestamp)] Cleaning containers and anonymous volumes on remote..."
for cname in "${CONTAINERS[@]}"; do
  docker rm -v "$cname" >/dev/null 2>&1 || true
done

if [[ "${CLEAN_IMAGE}" == "true" ]]; then
  echo "[$(timestamp)] Removing remote image: $IMAGE"
  docker rmi "$IMAGE" >/dev/null 2>&1 || true
fi

# Disarm trap (we already cleaned)
trap - EXIT INT TERM

# --------- SUMMARY ---------
echo
echo "Summary:"
fail=0
for cname in "${CONTAINERS[@]}"; do
  code="${EXITCODES[$cname]}"
  printf '  %-30s  exit %s\n' "${JOB2NAME[$cname]}" "$code"
  [[ "$code" != "0" ]] && fail=1
done

echo
if [[ "$fail" -ne 0 ]]; then
  echo "One or more jobs FAILED. Check ${OUT_DIR}/*/container.log for details." >&2
  exit 1
else
  echo "All jobs succeeded. Artifacts & logs are in: ${OUT_DIR}/"
fi
