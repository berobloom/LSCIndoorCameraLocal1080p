# Variables
SDCARD_DIR="/mnt"
SDCARD_DEV="/dev/mmcblk0p1"
DATA_DIR="${SDCARD_DIR}/data"
WEB_DIR="${DATA_DIR}/web"
DEBUG_FILE="${SDCARD_DIR}/output.log"
ENV_VARS="${SDCARD_DIR}/env"
WPA_FILE="/tmp/wpa_supplicant.conf"
WEB_PORT=80

# Busybox applets
BUSYBOX="${SDCARD_DIR}/busybox"
BASE64="${BUSYBOX} base64"
GREP="${BUSYBOX} grep"
AWK="${BUSYBOX} awk"
NTPD="${BUSYBOX} ntpd"
MKFIFO="${BUSYBOX} mkfifo"
PIDOF="${BUSYBOX} pidof"
HTTPD="${BUSYBOX} httpd"

# Guino applications
REREDIRECT="${DATA_DIR}/reredirect"

# Functions
reboot_proc () {
    echo "${1}"
    reboot
    exit 1
}

# Cleanup /etc/conf
echo "Cleanup /etc/conf..."
rm -rf /etc/conf/Config \
       /etc/conf/tuya \
       /etc/conf/reboot.log \
       /etc/conf/custom \
       /etc/conf/product.cof

# Check for SD Card
echo "Check for sd card..."
if [[ -e "${SDCARD_DEV}" ]]
then
    mount "${SDCARD_DEV}" "${SDCARD_DIR}"
else
    reboot_proc "Could not find sd card"
fi

# Check for product.cof
echo "Check for ${SDCARD_DIR}/product.cof..."
if [[ ! -f "${SDCARD_DIR}/product.cof" ]]
then
    reboot_proc "Could not find ${SDCARD_DIR}/product.cof"
fi

# Check for stationssid and stationpwd
# This is the magic state in order to run a local TUTK server
echo "Check for stationssid and stationpwd..."
if ! ${GREP} "\[STATION\]" -A1 ${SDCARD_DIR}/product.cof | ${GREP} -q stationssid\=
then
    reboot_proc "Please set stationssid and stationpwd correctly in ${SDCARD_DIR}/product.cof"
fi
if ! ${GREP} "\[STATION\]" -A2 ${SDCARD_DIR}/product.cof | ${GREP} -q stationpwd\=
then
    reboot_proc "Please set stationssid and stationpwd correctly in ${SDCARD_DIR}/product.cof"
fi

# Connect to WiFi.
echo "Connect to WiFi..."
ssid=$(${GREP} stationssid= ${SDCARD_DIR}/product.cof | ${AWK} -F'=' '{print $2}')
ssid_pwd=$(${GREP} stationpwd= ${SDCARD_DIR}/product.cof | ${AWK} -F'=' '{print $2}')
rm -f "${WPA_FILE}"
cat <<EOF >> "${WPA_FILE}"
ctrl_interface=/var/run/wpa_supplicant

network={
        ssid="${ssid}"
        proto=WPA RSN
        key_mgmt=WPA-PSK
        pairwise=TKIP CCMP
        group=TKIP CCMP
        psk="${ssid_pwd}"
        priority=1
}
EOF
ifconfig wlan0 up
sleep 5
wpa_supplicant -B -i wlan0 -c "${WPA_FILE}"
sleep 5
udhcpc -i wlan0

# Get environment variables
echo "Get environment variables..."
if [[ -f "${ENV_VARS}" ]]
then
    source "${ENV_VARS}"
fi

# Set time server.
# WARNING: If time can not be synced, it will reboot
# When issues with time occur, set SKIPTIME to true in /mnt/env
# This will however result in a wrong time burned in the stream
if [[ "${SKIPTIME}" == "false" ]]
then
    echo "Try to sync time..."
    ${NTPD} -l -p "${TIMESERVER}"
    retry_count=0

    while true
    do
        current_date=$(date)
        if echo "$current_date" | ${GREP} -q "1970"
        then
            echo "Wait for time sync"
            retry_count=$((retry_count+1))
            if [ $retry_count -ge 60 ]; then
                reboot_proc "Max retry count (60) reached. Exiting."
            fi
        else
            echo "Time synced"
            break
        fi
        sleep 1
    done
fi

# Start the main application
echo "Start main application..."
cd /usr/bin
./dgiot&

sleep 30

# Stripped custom.sh sourced from https://github.com/guino/LSC1080P/blob/main/mmc/custom.sh
DGIOT_PID=$(${PIDOF} dgiot)
${MKFIFO} /tmp/log
# Redirect logs to /tmp/log for debugging
${REREDIRECT} -m /tmp/log ${DGIOT_PID} > /tmp/redir.log

# Start HTTPD Server
BASE64_CREDENTIALS="$(${BASE64 }${HTTP_USER}:${HTTP_PASS})"
echo "/${BASE64_CREDENTIALS}" > "${WEB_DIR}/httpd.conf"
${HTTPD} -c "${WEB_DIR}/httpd.conf" -h "${WEB_DIR}" -p ${WEB_PORT}