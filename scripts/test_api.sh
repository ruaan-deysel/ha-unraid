#!/bin/bash
# Curl-based script to test the Unraid GraphQL API
# Supports all three SSL/TLS modes: No, Yes, Strict

# Configuration (default values)
SERVER_IP=""
API_KEY=""
QUERY_TYPE="info"
SSL_MODE="auto"  # auto, no, yes, strict

# Help message
show_help() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -i, --ip         Server IP address (required)"
    echo "  -k, --key        API key (required)"
    echo "  -t, --type       Query type: info, array, docker, disks, network, shares, vms,"
    echo "                   notifications, users, apikeys, memory, cpu, ups, disk-sleep,"
    echo "                   system-uptime, array-usage, disk-health, parity-status (default: info)"
    echo "  -s, --ssl        SSL/TLS mode: auto, no, yes, strict (default: auto)"
    echo "                   - auto: Auto-detect by checking for redirects"
    echo "                   - no: HTTP only (Unraid SSL/TLS = No)"
    echo "                   - yes: HTTPS with self-signed cert (Unraid SSL/TLS = Yes)"
    echo "                   - strict: HTTPS via myunraid.net (Unraid SSL/TLS = Strict)"
    echo ""
    echo "SSL/TLS Modes Explained:"
    echo "  When Unraid's Settings > Management Access > SSL/TLS is set to:"
    echo "  - 'No': Server only accepts HTTP connections on local IP"
    echo "  - 'Yes': Server redirects to HTTPS with self-signed certificate"
    echo "  - 'Strict': Server redirects to myunraid.net with Let's Encrypt cert"
    echo ""
    echo "Examples:"
    echo "  $0 -i 192.168.1.100 -k YOUR_API_KEY --type info"
    echo "  $0 -i 192.168.1.100 -k YOUR_API_KEY --ssl no"
    echo "  $0 -i 192.168.1.100 -k YOUR_API_KEY --ssl yes --type docker"
    echo "  $0 -i 192.168.1.100 -k YOUR_API_KEY --ssl strict --type array"
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
        -s|--ssl)
            SSL_MODE="$2"
            shift
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

echo "============================================="
echo "Unraid GraphQL API Test"
echo "============================================="
echo "Server IP: $SERVER_IP"
echo "Query: $TITLE"
echo "SSL Mode: $SSL_MODE"
echo "---------------------------------------------"

# Determine the URL and curl options based on SSL mode
CURL_OPTS="-s"
GRAPHQL_URL=""
DOMAIN=""

case $SSL_MODE in
    no)
        # SSL/TLS = No: Direct HTTP connection
        echo "Mode: HTTP only (SSL/TLS = No)"
        GRAPHQL_URL="http://$SERVER_IP/graphql"
        DOMAIN="$SERVER_IP"
        ;;
    yes)
        # SSL/TLS = Yes: HTTPS with self-signed certificate
        echo "Mode: HTTPS with self-signed cert (SSL/TLS = Yes)"
        GRAPHQL_URL="https://$SERVER_IP/graphql"
        DOMAIN="$SERVER_IP"
        CURL_OPTS="$CURL_OPTS -k"  # Allow insecure (self-signed cert)
        ;;
    strict)
        # SSL/TLS = Strict: Check for myunraid.net redirect
        echo "Mode: HTTPS via myunraid.net (SSL/TLS = Strict)"
        echo "Checking for redirect..."
        REDIRECT_URL=$(curl -s -I -k "http://$SERVER_IP/graphql" 2>/dev/null | grep -i "^Location:" | awk '{print $2}' | tr -d '\r\n')

        if [ -n "$REDIRECT_URL" ] && [[ "$REDIRECT_URL" == *"myunraid.net"* ]]; then
            echo "Found myunraid.net redirect: $REDIRECT_URL"
            GRAPHQL_URL="$REDIRECT_URL"
            DOMAIN=$(echo "$REDIRECT_URL" | sed -E 's|https?://([^/]+).*|\1|')
        else
            echo "Warning: No myunraid.net redirect found. Trying direct HTTPS..."
            GRAPHQL_URL="https://$SERVER_IP/graphql"
            DOMAIN="$SERVER_IP"
            CURL_OPTS="$CURL_OPTS -k"
        fi
        ;;
    auto|*)
        # Auto-detect: Check what kind of redirect we get
        echo "Mode: Auto-detecting SSL/TLS configuration..."

        # First, try HTTP and check for redirect
        HTTP_RESPONSE=$(curl -s -I -o /dev/null -w "%{http_code}" "http://$SERVER_IP/graphql" 2>/dev/null)
        REDIRECT_URL=$(curl -s -I "http://$SERVER_IP/graphql" 2>/dev/null | grep -i "^Location:" | awk '{print $2}' | tr -d '\r\n')

        echo "HTTP response code: $HTTP_RESPONSE"

        if [ "$HTTP_RESPONSE" = "302" ] || [ "$HTTP_RESPONSE" = "301" ]; then
            if [ -n "$REDIRECT_URL" ]; then
                echo "Found redirect: $REDIRECT_URL"

                if [[ "$REDIRECT_URL" == *"myunraid.net"* ]]; then
                    # SSL/TLS = Strict (myunraid.net)
                    echo "Detected: SSL/TLS = Strict (myunraid.net)"
                    GRAPHQL_URL="$REDIRECT_URL"
                    DOMAIN=$(echo "$REDIRECT_URL" | sed -E 's|https?://([^/]+).*|\1|')
                elif [[ "$REDIRECT_URL" == https://* ]]; then
                    # SSL/TLS = Yes (HTTPS redirect to same IP)
                    echo "Detected: SSL/TLS = Yes (self-signed cert)"
                    GRAPHQL_URL="$REDIRECT_URL"
                    DOMAIN=$(echo "$REDIRECT_URL" | sed -E 's|https?://([^/]+).*|\1|')
                    CURL_OPTS="$CURL_OPTS -k"  # Allow insecure
                else
                    # Some other redirect
                    echo "Detected: Unknown redirect, following..."
                    GRAPHQL_URL="$REDIRECT_URL"
                    DOMAIN=$(echo "$REDIRECT_URL" | sed -E 's|https?://([^/]+).*|\1|')
                fi
            fi
        elif [ "$HTTP_RESPONSE" = "200" ] || [ "$HTTP_RESPONSE" = "400" ]; then
            # HTTP returned 200 or 400 (GraphQL expects POST, so GET returns 400)
            # This means SSL/TLS = No
            echo "Detected: SSL/TLS = No (HTTP only)"
            GRAPHQL_URL="http://$SERVER_IP/graphql"
            DOMAIN="$SERVER_IP"
        else
            # Fallback to HTTPS with insecure
            echo "Could not detect mode (HTTP code: $HTTP_RESPONSE), trying HTTPS..."
            GRAPHQL_URL="https://$SERVER_IP/graphql"
            DOMAIN="$SERVER_IP"
            CURL_OPTS="$CURL_OPTS -k"
        fi
        ;;
esac

echo ""
echo "Using URL: $GRAPHQL_URL"
echo "Domain: $DOMAIN"
echo "---------------------------------------------"

# Execute the GraphQL query using curl
# Using jq for pretty output if available
if command -v jq &> /dev/null; then
    curl $CURL_OPTS -L \
      -X POST \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -H "Origin: https://$DOMAIN" \
      -H "Host: $DOMAIN" \
      -H "Referer: https://$DOMAIN/dashboard" \
      -d "$QUERY" \
      "$GRAPHQL_URL" | jq '.'
    CURL_EXIT=$?
else
    curl $CURL_OPTS -L \
      -X POST \
      -H "Content-Type: application/json" \
      -H "x-api-key: $API_KEY" \
      -H "Origin: https://$DOMAIN" \
      -H "Host: $DOMAIN" \
      -H "Referer: https://$DOMAIN/dashboard" \
      -d "$QUERY" \
      "$GRAPHQL_URL"
    CURL_EXIT=$?
fi

echo ""
echo "---------------------------------------------"

if [ $CURL_EXIT -eq 0 ]; then
    echo "✅ Query completed successfully"
else
    echo "❌ Query failed with exit code: $CURL_EXIT"
fi
echo "---------------------------------------------"
