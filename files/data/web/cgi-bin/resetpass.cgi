#!/bin/sh

# Set the Content-type header
echo "Content-type: text/html"
echo

NEW_USERNAME=$(/mnt/busybox tr -dc 'a-zA-Z0-9' < /dev/urandom | /mnt/busybox head -c 6)
NEW_PASSWORD=$(/mnt/busybox tr -dc 'a-zA-Z0-9' < /dev/urandom | /mnt/busybox head -c 6)

cp /usr/bin/dgiot /mnt/dgiot_new
sed -i "s/defusr/${NEW_USERNAME}/g" /mnt/dgiot_new
sed -i "s/defpwd/${NEW_PASSWORD}/g" /mnt/dgiot_new

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

mv /mnt/dgiot_new /mnt/dgiot
sync
reboot
