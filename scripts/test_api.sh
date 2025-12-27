#!/bin/bash
# Curl-based script to test the Unraid GraphQL API

# Configuration (default values)
SERVER_IP=""
API_KEY=""
QUERY_TYPE="info"
DIRECT_IP=false

# Help message
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -i, --ip         Server IP address (default: $SERVER_IP)"
    echo "  -k, --key        API key (default: predefined key)"
    echo "  -t, --type       Query type: info, array, docker, disks, network, shares, vms,"
    echo "                   notifications, users, apikeys, memory, cpu, ups, disk-sleep,
                   system-uptime, array-usage, disk-health, parity-status (default: info)"
    echo "  -d, --direct     Use direct IP connection without checking for redirects"
    echo ""
    echo "Examples:"
    echo "  $0 --type info"
    echo "  $0 --ip 192.168.1.100 --type docker"
    echo "  $0 --ip 192.168.1.100 --direct"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--ip)
            SERVER_IP="$2"
            shift
            shift
            ;;
        -k|--key)
            API_KEY="$2"
            shift
            shift
            ;;
        -t|--type)
            QUERY_TYPE="$2"
            shift
            shift
            ;;
        -d|--direct)
            DIRECT_IP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Define queries
INFO_QUERY='{
  "query": "{ info { cpu { id manufacturer brand cores threads } memory { layout { size bank type clockSpeed manufacturer } } versions { core { unraid api kernel } packages { openssl node npm } } } }"
}'

ARRAY_QUERY='{
  "query": "{ array { state capacity { kilobytes { free used total } disks { free used total } } boot { name device size temp type } parities { name device size status type } disks { name device size status type temp fsSize fsFree fsUsed } caches { name device size temp status type fsSize fsFree fsUsed } } }"
}'

DOCKER_QUERY='{
  "query": "{ docker { containers { id names image state status autoStart ports { ip privatePort publicPort type } } } }"
}'

# WARNING: The physical 'disks' endpoint with temperature/smartStatus WAKES sleeping disks!
# This query only gets safe fields that don't wake disks
DISKS_QUERY='{
  "query": "{ disks { id device name type size vendor firmwareRevision serialNum interfaceType isSpinning partitions { name fsType size } } }"
}'

# Network info is available via server query (no standalone network query exists)
NETWORK_QUERY='{
  "query": "{ server { id name wanip lanip localurl remoteurl status } }"
}'

SHARES_QUERY='{
  "query": "{ shares { name comment free size used } }"
}'

VMS_QUERY='{
  "query": "{ vms { domain { uuid name state } } }"
}'

NOTIFICATIONS_QUERY='{
  "query": "{ notifications { list(filter: { type: UNREAD, offset: 0, limit: 10 }) { id title subject description importance link type timestamp formattedTimestamp } overview { unread { info warning alert total } archive { info warning alert total } } } }"
}'

USERS_QUERY='{
  "query": "{ me { id name description roles } }"
}'

APIKEYS_QUERY='{
  "query": "{ apiKeys { id name description roles createdAt permissions { resource actions } } }"
}'

MEMORY_QUERY='{
  "query": "{ info { memory { layout { size bank type clockSpeed manufacturer } } } }"
}'

CPU_QUERY='{
  "query": "{ info { cpu { id manufacturer brand cores threads clockSpeed architecture flags } } }"
}'

UPS_QUERY='{
  "query": "{ upsDevices { id name model status battery { chargeLevel estimatedRuntime health } power { inputVoltage outputVoltage loadPercentage } } }"
}'

# Safe query - only uses array.disks which doesn't wake sleeping disks
# The physical 'disks' endpoint is NOT queried here to avoid waking disks
DISK_SLEEP_QUERY='{
  "query": "{ array { disks { name device isSpinning rotational temp status } parities { name device isSpinning rotational temp status } caches { name device isSpinning rotational temp status } } }"
}'

SYSTEM_UPTIME_QUERY='{
  "query": "{ info { os { uptime hostname platform distro release kernel arch } } }"
}'

ARRAY_USAGE_QUERY='{
  "query": "{ array { state disks { name device size fsUsed fsFree fsType } parities { name device size } caches { name device size fsUsed fsFree fsType } } }"
}'

DISK_HEALTH_QUERY='{
  "query": "{ array { disks { name device size temp status numErrors numReads numWrites rotational } parities { name device size temp status numErrors numReads numWrites rotational } caches { name device size temp status numErrors numReads numWrites rotational } } }"
}'

PARITY_STATUS_QUERY='{
  "query": "{ parityHistory { date duration speed status errors progress correcting paused running } }"
}'

# Set the query based on type
case $QUERY_TYPE in
    info)
        QUERY=$INFO_QUERY
        TITLE="Server Information"
        ;;
    array)
        QUERY=$ARRAY_QUERY
        TITLE="Array Status"
        ;;
    docker)
        QUERY=$DOCKER_QUERY
        TITLE="Docker Containers"
        ;;
    disks)
        QUERY=$DISKS_QUERY
        TITLE="Disk Information"
        ;;
    network)
        QUERY=$NETWORK_QUERY
        TITLE="Network Information"
        ;;
    shares)
        QUERY=$SHARES_QUERY
        TITLE="Shares Information"
        ;;
    vms)
        QUERY=$VMS_QUERY
        TITLE="Virtual Machines"
        ;;
    notifications)
        QUERY=$NOTIFICATIONS_QUERY
        TITLE="Notifications"
        ;;
    users)
        QUERY=$USERS_QUERY
        TITLE="Current User"
        ;;
    apikeys)
        QUERY=$APIKEYS_QUERY
        TITLE="API Keys"
        ;;
    memory)
        QUERY=$MEMORY_QUERY
        TITLE="Memory Information"
        ;;
    cpu)
        QUERY=$CPU_QUERY
        TITLE="CPU Information"
        ;;
    ups)
        QUERY=$UPS_QUERY
        TITLE="UPS Devices"
        ;;
    disk-sleep)
        QUERY=$DISK_SLEEP_QUERY
        TITLE="Disk Sleep Status"
        ;;
    system-uptime)
        QUERY=$SYSTEM_UPTIME_QUERY
        TITLE="System Uptime"
        ;;
    array-usage)
        QUERY=$ARRAY_USAGE_QUERY
        TITLE="Array Usage Summary"
        ;;
    disk-health)
        QUERY=$DISK_HEALTH_QUERY
        TITLE="Disk Health Status"
        ;;
    parity-status)
        QUERY=$PARITY_STATUS_QUERY
        TITLE="Parity Check Status"
        ;;
    *)
        echo "Unknown query type: $QUERY_TYPE"
        show_help
        exit 1
        ;;
esac

echo "Connecting to Unraid at $SERVER_IP to query $TITLE..."
echo "---------------------------------------------"

# Check for redirect first
REDIRECT_URL=""
if [ "$DIRECT_IP" = false ]; then
    echo "Checking for redirect..."
    REDIRECT_URL=$(curl -s -I "http://$SERVER_IP/graphql" | grep -i "Location:" | awk '{print $2}' | tr -d '\r')

    if [ -n "$REDIRECT_URL" ]; then
        echo "Found redirect URL: $REDIRECT_URL"
        # Extract domain for headers
        DOMAIN=$(echo "$REDIRECT_URL" | sed -E 's|https?://([^/]+).*|\1|')
        echo "Using domain: $DOMAIN for headers"
    else
        echo "No redirect found, using direct IP"
        DOMAIN="$SERVER_IP"
        REDIRECT_URL="http://$SERVER_IP/graphql"
    fi
else
    echo "Using direct IP as requested"
    DOMAIN="$SERVER_IP"
    REDIRECT_URL="http://$SERVER_IP/graphql"
fi

# Execute the GraphQL query using curl and follow redirects
# Adding -s for silent operation (removes progress bar) but keeping errors
# Using jq for pretty output if available
if command -v jq &> /dev/null; then
    curl -s -L \
      -X POST \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -H "Origin: https://$DOMAIN" \
      -H "Host: $DOMAIN" \
      -H "Referer: https://$DOMAIN/dashboard" \
      -d "$QUERY" \
      "$REDIRECT_URL" | jq '.'
else
    curl -L \
      -X POST \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -H "Origin: https://$DOMAIN" \
      -H "Host: $DOMAIN" \
      -H "Referer: https://$DOMAIN/dashboard" \
      -d "$QUERY" \
      "$REDIRECT_URL"
fi

echo ""
echo "---------------------------------------------"