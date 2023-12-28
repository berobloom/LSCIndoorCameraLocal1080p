#!/bin/sh

# Set the Content-type header
echo "Content-type: text/html"
echo

NEW_USERNAME=$(/mnt/busybox tr -dc 'a-zA-Z0-9' < /dev/urandom | /mnt/busybox head -c 6)
NEW_PASSWORD=$(/mnt/busybox tr -dc 'a-zA-Z0-9' < /dev/urandom | /mnt/busybox head -c 6)

cd /mnt
rm -f dgiot_new
sync

cp base_app/dgiot dgiot_new
sync
sed -i "s/defusr/${NEW_USERNAME}/g" dgiot_new
sed -i "s/defpwd/${NEW_PASSWORD}/g" dgiot_new
sync

echo "<html>"
echo "<head>"
echo "<title>New TUTK Credentials</title>"
echo "</head>"
echo "<body>"

echo "<p>Your new TUTK username: <strong>${NEW_USERNAME}</strong></p>"
echo "<p>Your new TUTK password: <strong>${NEW_PASSWORD}</strong></p>"
echo "<p>Make sure to update the \"settings.yaml\" when you use LSCProxy</p>"
echo "<br>"
echo "<p>Rebooting camera to apply changes...</p>"

echo "</body>"
echo "</html>"

mv dgiot_new dgiot
sync
reboot
