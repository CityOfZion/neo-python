#!/bin/bash
PROMPT_OPTS=()
BOOTSTRAP_OPTS=()
BOOTSTRAP=false

if [[ "${@#-c}" != "$@" ]] && [[ "${@#*-m*}" != "$@" ]]; then
    echo "Error: can not use config file on main net" >&2
    exit 126
fi

if [[ "${@#--bootstrap}" != "$@" ]] && [[ "${@#*-p*}" != "$@" ]]; then
    echo "Error: can not bootstrap on private net" >&2
    exit 126
elif [[ "${@#--bootstrap}" != "$@" ]] && [[ "${@#--coznet}" != "$@" ]]; then
    echo "Error: can not bootstrap on coz net" >&2
    exit 126
fi

if [[ "${@#--bootstrap}" = "$@" ]] && [[ "${@#*-n*}" != "$@" ]]; then
    echo "Error: -n / --notifications option can only be used in case --bootstrap is used as well" >&2
    exit 126
fi

while [ -n "$1" ]; do
    case "$1" in
        -m|--mainnet)
            PROMPT_OPTS+="-m"
            BOOTSTRAP_OPTS+="-m"
        ;;
        -p|--privnet)
            PROMPT_OPTS+="-p"
        ;;
        --coznet)
            PROMPT_OPTS+="--coznet"
        ;;
        -c|--config)
            shift
            PROMPT_OPTS+="-c=$1"
            BOOTSTRAP_OPTS+="-c=$1"
        ;;
        -t|--set-default-theme)
            shift
            PROMPT_OPTS+="-t=$1"
        ;;
        --version)
            shift
            PROMPT_OPTS+="--version=$1"
        ;;
        --bootstrap)
            BOOTSTRAP=true
        ;;
        -n|--notifications)
            BOOTSTRAP_OPTS+="-n"
        ;;
        esac
        shift
done

rm -rf /neo-python/Chains/privatenet
if [ ! -d "/neo-python/Chains/SC234" ] && [[ "$BOOTSTRAP" = true ]]; then
  python3 /neo-python/bootstrap.py --skipconfirm "${BOOTSTRAP_OPTS[@]}"
fi

python3 /neo-python/prompt.py "${PROMPT_OPTS[@]}"
