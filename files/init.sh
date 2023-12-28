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
    echo "${1}" > "${SDCARD_DIR}/last_boot_error.log"
    reboot
    exit 1
}

# Check for SD Card
echo "Check for sd card..."
if [[ -e "${SDCARD_DEV}" ]]
then
    mount "${SDCARD_DEV}" "${SDCARD_DIR}"
else
    reboot_proc "Could not find sd card"
fi

# Check for base dgiot
echo "Check for base dgiot app..."
if [[ ! -f "${SDCARD_DIR}/base_app/dgiot" ]]
then
    reboot_proc "Could not find base dgiot app"
fi

# Check if dgiot exists
if [[ ! -f "${SDCARD_DIR}/dgiot" ]]
then
    cp "${SDCARD_DIR}/base_app/dgiot" "${SDCARD_DIR}/dgiot"
    sync
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

# Start HTTPD Server
echo "/:${HTTPD_USER}:${HTTPD_PASS}" > "${WEB_DIR}/httpd.conf"
${HTTPD} -c "${WEB_DIR}/httpd.conf" -h "${WEB_DIR}" -p ${WEB_PORT}
