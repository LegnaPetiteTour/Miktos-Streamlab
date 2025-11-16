# 📱 Complete Android App Testing Guide for Beginners

This guide will walk you through testing the Miktos StreamLab Camera Android app step-by-step.

---

## 🎯 What You'll Need

- ✅ Your Android phone (any model)
- ✅ USB cable (to connect phone to Mac)
- ✅ Your Mac computer
- ✅ Both devices on the same Wi-Fi network

**Estimated Time:** 15-20 minutes

---

## 📋 Part 1: Enable Developer Mode on Your Android Phone

### Step 1.1: Find Your Build Number

1. **Open Settings** on your Android phone
2. **Scroll down** and tap **"About phone"** (or "About device")
   - On Samsung: Settings → About phone
   - On Google Pixel: Settings → About phone
   - On other brands: May be under System → About phone

3. **Look for "Build number"** (might be under "Software information")

### Step 1.2: Enable Developer Mode

1. **Tap "Build number" 7 times rapidly**
   - You'll see a countdown: "You are now 3 steps away from being a developer..."
   - Keep tapping until you see: **"You are now a developer!"**

2. **Go back** to the main Settings screen

3. **Find "Developer options"**
   - On Samsung: Settings → Developer options
   - On Google Pixel: Settings → System → Developer options
   - It should now be visible in your Settings

### Step 1.3: Enable USB Debugging

1. **Open Developer options**

2. **Turn on "USB debugging"**
   - Toggle the switch to ON
   - You'll see a warning popup: **"Allow USB debugging?"**
   - Tap **"OK"**

3. **Keep this screen open** for now

---

## 🔌 Part 2: Connect Your Phone to Mac

### Step 2.1: Physical Connection

1. **Get your USB cable** (the one you use to charge your phone)

2. **Connect one end to your phone**

3. **Connect the other end to your Mac**

### Step 2.2: Authorize the Connection

**On Your Phone:**

- A popup will appear: **"Allow USB debugging?"**
- It shows your Mac's RSA key fingerprint
- ✅ **Check "Always allow from this computer"**
- ✅ **Tap "OK"** or "Allow"

**Important:** If you don't see this popup, try:

- Unlocking your phone screen
- Changing the USB mode: Pull down notification shade → Tap USB notification → Select "File Transfer" or "MTP"

### Step 2.3: Verify Connection

1. **Open Terminal on your Mac:**
   - Press `Cmd + Space`
   - Type "Terminal"
   - Press Enter

2. **Type this command and press Enter:**

   ```bash
   adb devices

   ```bash

3. **You should see something like:**

   ```text
   List of devices attached
   ABC123DEF456    device

   ```bash

   **If you see your device listed with "device" next to it:** ✅ **SUCCESS!** Continue to Part 3.

   **If you see "unauthorized":** Go back to your phone and approve the USB debugging popup.

   **If you see nothing:** Try:

   - Disconnect and reconnect the USB cable
   - Try a different USB port on your Mac
   - Make sure your cable supports data transfer (not just charging)

---

## 📱 Part 3: Install the App on Your Phone

### Step 3.1: Open Terminal (if not already open)

If you closed Terminal, open it again:

- Press `Cmd + Space`
- Type "Terminal"
- Press Enter

### Step 3.2: Navigate to the Android Project

**Copy and paste** this command into Terminal and press Enter:

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Mobile/Android"

```bash

### Step 3.3: Install the App

**Copy and paste** this command and press Enter:

```bash
./gradlew installDebug

```bash

**What you'll see:**

- The command will start downloading and building
- You'll see progress messages scrolling
- After 10-30 seconds, you should see: **BUILD SUCCESSFUL**

**On your phone:**

- You'll see a notification: "App installed"
- The **Miktos Camera** app will appear in your app drawer

---

## 🖥️ Part 4: Set Up Your Mac to Receive the Stream

### Step 4.1: Get Your Mac's IP Address

**In Terminal**, type this command and press Enter:

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1

```bash

**You'll see something like:**

```bash
inet 192.168.2.36 netmask 0xffffff00 broadcast 192.168.2.255

```bash

**Write down the IP address:** In this example, it's **192.168.2.36**

- Your IP will be different!
- It usually starts with 192.168 or 10.0

### Step 4.2: Start the Video Receiver on Your Mac

**Open a NEW Terminal window:**

- Press `Cmd + N` in Terminal, or
- Press `Cmd + Space`, type "Terminal", press Enter

**In the new Terminal window**, run these commands:

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab"
source .venv/bin/activate
python3 tcp_h264_receiver.py

```bash

**You should see:**

```bash
🎥 TCP H.264 Receiver started on 0.0.0.0:8554
Waiting for Android StreamLab Camera connection...

```bash

**Leave this Terminal window open** - this is your receiver waiting for the phone to connect.

---

## 📺 Part 5: Test the Streaming

### Step 5.1: Open the App on Your Phone

1. **Unlock your phone**
2. **Open the app drawer** (swipe up or tap the apps icon)
3. **Find and tap "Miktos Camera"**

### Step 5.2: Grant Permissions

The app will ask for permissions. **Grant them all:**

1. **Camera permission**
   - Tap "Allow" or "While using the app"

2. **Microphone permission**
   - Tap "Allow" or "While using the app"

3. **Notification permission** (Android 13+)
   - Tap "Allow"

### Step 5.3: Configure the Streaming Settings

**In the app, you'll see two input fields:**

1. **Mac IP Address:**
   - Tap the first text box
   - **Enter your Mac's IP address** (from Step 4.1)
   - Example: `192.168.2.36`

2. **Port:**
   - Should already show `8554`
   - **Don't change it**

### Step 5.4: Start Streaming

1. **Tap the green "START STREAMING" button**

2. **On your phone, you'll see:**
   - Button turns red and says "STOP STREAMING"
   - Status shows: "✅ LIVE: Streaming to 192.168.2.36:8554"
   - A notification appears: "📹 Streaming to Mac..."

3. **On your Mac Terminal, you'll see:**

   ```text
   ✅ Connected to 192.168.2.XX:XXXXX at 2025-11-15 18:30:45
   📊 Receiving stream... 2.5 MB/s (150 frames/s)

   ```bash

**Congratulations! You're streaming!** 🎉

---

## 🎬 Part 6: What You Can Do Now

### Test the Camera Stream

1. **Move your phone around** - you'll see the bitrate/frame rate in Terminal
2. **Point the camera at different things**
3. **Check the notification** - it shows streaming status

### Test Auto-Reconnection

1. **Turn off Wi-Fi on your phone** (swipe down, tap Wi-Fi icon)
2. **Watch the Terminal** - it will show disconnection
3. **Turn Wi-Fi back on**

4. **The app will auto-reconnect!** (up to 3 attempts)

### Stop Streaming

1. **Tap the red "STOP STREAMING" button** on your phone
2. Terminal will show disconnection
3. Button turns green again, ready for next stream

---

## ❓ Troubleshooting

### Problem: "adb devices" shows nothing

**Solution:**

1. Disconnect and reconnect USB cable
2. On phone: Settings → Developer Options → Revoke USB debugging authorizations → Re-authorize
3. Try a different USB cable (must support data, not just charging)

4. Install Android Platform Tools: `brew install android-platform-tools`

### Problem: Can't find Developer Options

**Solution:**

1. Make sure you tapped Build Number exactly 7 times
2. Look in different places:
   - Settings → System → Developer options
   - Settings → System → Advanced → Developer options
3. Search in Settings for "developer"

### Problem: Terminal shows "Connection refused"

**Solution:**

1. **Check Wi-Fi:** Both phone and Mac must be on the SAME Wi-Fi network
2. **Check IP address:** Make sure you entered the correct Mac IP in the app
3. **Check receiver:** Make sure `tcp_h264_receiver.py` is still running in Terminal

4. **Check port:** Should be 8554 on both sides

### Problem: App crashes or won't start

**Solution:**

1. Grant all permissions (Camera, Microphone, Notifications)
2. Restart the app
3. Reinstall: `cd "/Users/atorrella/Desktop/Miktos Streamlab/Mobile/Android" && ./gradlew installDebug`

### Problem: Stream connects but no video/low quality

**Solution:**

1. **Good lighting:** Phone camera needs good light
2. **Stable Wi-Fi:** Move closer to Wi-Fi router
3. **Background apps:** Close other apps using camera/network

4. **Check Terminal:** Look for bitrate - should be 5-6 Mbps

---

## 📝 Quick Command Reference

### Check Connected Devices

```bash
adb devices

```bash

### Install App

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab/Mobile/Android"
./gradlew installDebug

```bash

### Get Mac IP Address

```bash
ifconfig | grep "inet " | grep -v 127.0.0.1

```bash

### Start Receiver

```bash
cd "/Users/atorrella/Desktop/Miktos Streamlab"
source .venv/bin/activate
python3 tcp_h264_receiver.py

```bash

### Uninstall App (if needed)

```bash
adb uninstall com.miktos.streamlabcamera

```bash

### View Phone Logs (advanced)

```bash
adb logcat | grep StreamLab

```bash

---

## ✅ Success Checklist

- [ ] Developer mode enabled on phone
- [ ] USB debugging enabled
- [ ] Phone connected and authorized (adb devices shows device)
- [ ] App installed on phone
- [ ] Mac IP address identified
- [ ] Receiver running on Mac
- [ ] All permissions granted in app
- [ ] Streaming successfully!

---

## 🎯 Next Steps After Testing

Once you've confirmed everything works:

1. **Test for 5-10 minutes** to verify stability
2. **Try disconnecting/reconnecting** to test auto-reconnection
3. **Test in different rooms** to check Wi-Fi range

4. **Document any issues** you encounter

---

## 💡 Pro Tips

1. **Keep phone plugged in** during long tests (streaming uses battery)
2. **Good Wi-Fi is crucial** - stay close to router for testing
3. **Check notification** - it shows real-time streaming status

4. **Terminal output** shows technical details (bitrate, frames, errors)
5. **Screen stays on** automatically during streaming

---

## 📞 Need Help?

If something doesn't work:

1. Read the Troubleshooting section above
2. Check both Terminal windows for error messages
3. Make sure both devices are on the same Wi-Fi

4. Try restarting both the app and the receiver

---

## Happy Streaming! 🎥📱
