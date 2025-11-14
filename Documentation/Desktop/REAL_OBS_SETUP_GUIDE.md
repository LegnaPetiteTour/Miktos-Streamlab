# 🎬 REAL OBS INTEGRATION GUIDE
**Miktos Streamlab - Week 3 Phase 2A**

---

## 🎯 OBJECTIVE

Validate your **107 passing tests** with a REAL OBS Studio instance!

---

## 📋 PREREQUISITES CHECKLIST

Before running the test, ensure you have:

- [ ] OBS Studio 28+ installed
- [ ] OBS Studio is running
- [ ] WebSocket server enabled in OBS
- [ ] WebSocket password configured
- [ ] At least 2 test scenes created
- [ ] `.env` file configured with password

---

## 🚀 QUICK START (5 Minutes)

### **Step 1: Install OBS (if needed)**
```bash
brew install --cask obs
```

### **Step 2: Open OBS**
```bash
open -a "OBS"
```

### **Step 3: Enable WebSocket**
1. Open OBS
2. Go to **Tools** → **WebSocket Server Settings**
3. Check **"Enable WebSocket server"**
4. Set **Port:** `4455`
5. Check **"Enable Authentication"**
6. Click **"Show Connect Info"** and copy the password
7. Click **OK**

### **Step 4: Configure Password**
Edit `.env` file:
```bash
nano .env
```

Replace `REPLACE_WITH_YOUR_PASSWORD` with your actual password, then save (Ctrl+X, Y, Enter)

### **Step 5: Create Test Scenes**

In OBS, create these scenes:

**1. Main Scene** (default)
- Add: Color Source (blue)
- Add: Text "MAIN SCENE - LIVE"

**2. Slate Scene** (new)
- Add: Color Source (red)
- Add: Text "TECHNICAL DIFFICULTIES"

**3. Camera Scene** (optional)
- Add: Color Source (green)
- Add: Text "CAMERA SCENE"

### **Step 6: Run the Test**
```bash
python test_real_obs.py
```

---

## 🧪 WHAT THE TEST DOES

The test script will automatically:

1. ✅ **Connect** to OBS Studio
2. ✅ **Get Version** and verify compatibility
3. ✅ **Monitor Health** (FPS, CPU, Memory)
4. ✅ **List Scenes** and show current scene
5. ✅ **Switch Scenes** between your test scenes
6. ✅ **Test Slate** display (show/hide)
7. ✅ **Check Streaming** status
8. ✅ **Disconnect** cleanly

---

## 📊 EXPECTED OUTPUT

### **Success:**
```
============================================================
🎬 MIKTOS STREAMLAB - REAL OBS INTEGRATION TEST
============================================================

============================================================
TEST 1: Connection
============================================================
✓ Successfully connected to OBS!

============================================================
TEST 2: OBS Version
============================================================
✓ OBS Version: 29.1.3
✓ OBS version is 28+ (WebSocket 5.x compatible)

[... more tests ...]

============================================================
TEST SUMMARY
============================================================
Connection................................... ✓ PASSED
Version Check................................ ✓ PASSED
Health Monitoring............................ ✓ PASSED
Scene Management............................. ✓ PASSED
Scene Switching.............................. ✓ PASSED
Slate Display................................ ✓ PASSED
Streaming Status............................. ✓ PASSED
Disconnection................................ ✓ PASSED

Results: 8/8 tests passed

🎉 ALL TESTS PASSED! 🎉
Your OBS integration is working perfectly!
```

---

## ❌ TROUBLESHOOTING

### **Problem: Connection Failed**

**Error:**
```
✗ Failed to connect to OBS!
```

**Solutions:**
1. **Is OBS running?**
   ```bash
   ps aux | grep OBS
   ```

2. **Is WebSocket enabled?**
   - Tools → WebSocket Server Settings
   - Check "Enable WebSocket server"

3. **Is password correct?**
   - In OBS: Tools → WebSocket Server Settings → Show Connect Info
   - Copy password to `.env` file

4. **Is port correct?**
   - Default is `4455`
   - Check `.env`: `OBS_PORT=4455`

5. **Firewall blocking?**
   ```bash
   # Test if port is open
   nc -zv localhost 4455
   ```

### **Problem: No Scenes Found**

**Error:**
```
✗ No scenes found!
```

**Solution:**
- Create at least one scene in OBS
- Default "Scene" should exist
- Click "+" in Scenes panel to create more

### **Problem: Scene Switching Failed**

**Error:**
```
✗ Scene mismatch! Expected Main, got Slate
```

**Solution:**
- Ensure scenes exist in OBS
- Scene names are case-sensitive
- Check spelling in test script

### **Problem: Version Not Compatible**

**Warning:**
```
⚠ OBS version is 27 (may not support all features)
```

**Solution:**
- Update OBS to version 28+
- WebSocket 5.x requires OBS 28+
```bash
brew upgrade --cask obs
```

### **Problem: Permission Denied**

**Error:**
```
OSError: [Errno 13] Permission denied
```

**Solution:**
```bash
# Make script executable
chmod +x test_real_obs.py

# Or run with python directly
python test_real_obs.py
```

---

## 🔍 DETAILED SETUP GUIDE

### **OBS WebSocket Configuration**

1. **Open OBS Studio**
   ```bash
   open -a "OBS"
   ```

2. **Navigate to WebSocket Settings**
   - Click **Tools** in menu bar
   - Select **WebSocket Server Settings**

3. **Configure Server**
   - ✅ Check "Enable WebSocket server"
   - Port: `4455` (default)
   - ✅ Check "Enable Authentication"
   - Click "Generate Password" (if needed)
   - Click "Show Connect Info"

4. **Copy Connection Info**
   ```
   Server: localhost
   Port: 4455
   Password: [your-password-here]
   ```

5. **Update .env File**
   ```bash
   OBS_HOST=localhost
   OBS_PORT=4455
   OBS_PASSWORD=your-actual-password
   ```

---

## 🎨 CREATING TEST SCENES

### **Scene 1: Main (Primary)**

1. Click **+** in Scenes panel
2. Name: "Main"
3. Add sources:
   - **Color Source**: Blue (#0000FF)
   - **Text (GDI+)**: "MAIN SCENE - LIVE"
     - Font: Arial Bold, 72pt
     - Color: White
     - Alignment: Center

### **Scene 2: Slate (Technical Difficulties)**

1. Click **+** in Scenes panel
2. Name: "Slate"
3. Add sources:
   - **Color Source**: Red (#FF0000)
   - **Text (GDI+)**: "TECHNICAL DIFFICULTIES"
     - Font: Arial Bold, 72pt
     - Color: White
     - Alignment: Center
   - **Text (GDI+)**: "Please Stand By"
     - Font: Arial, 48pt
     - Color: White
     - Alignment: Center
     - Position: Below main text

### **Scene 3: Camera (Optional)**

1. Click **+** in Scenes panel
2. Name: "Camera"
3. Add sources:
   - **Color Source**: Green (#00FF00)
   - **Text (GDI+)**: "CAMERA SCENE"

---

## 📝 VALIDATION CHECKLIST

After running the test, verify:

### **Connection**
- [ ] Connected to OBS without errors
- [ ] Status shows "connected"

### **Version**
- [ ] OBS version is 28 or higher
- [ ] WebSocket 5.x compatible

### **Health**
- [ ] FPS shows actual framerate (30 or 60)
- [ ] CPU usage shows percentage
- [ ] Memory usage shows MB used

### **Scenes**
- [ ] All scenes listed correctly
- [ ] Current scene identified
- [ ] Scene names match OBS

### **Scene Switching**
- [ ] Can switch between scenes
- [ ] Current scene updates correctly
- [ ] Visual change visible in OBS

### **Slate Display**
- [ ] Slate scene can be activated
- [ ] Returns to main scene correctly
- [ ] Smooth transitions

### **Streaming Status**
- [ ] Shows correct streaming state
- [ ] If streaming, shows stats
- [ ] Frame counts accurate

### **Disconnection**
- [ ] Disconnects cleanly
- [ ] No errors on exit
- [ ] Status shows "disconnected"

---

## 🎯 SUCCESS CRITERIA

**Your OBS integration is SUCCESSFUL if:**

✅ **All 8 tests pass** (8/8)  
✅ **No connection errors**  
✅ **Scene switching works**  
✅ **Health monitoring accurate**  
✅ **Slate display functions**  

**If ANY test fails, review troubleshooting section above.**

---

## 🚀 NEXT STEPS AFTER SUCCESS

Once all tests pass:

1. ✅ **Document Results** - Save test output
2. ✅ **Test Streaming** - Try actual streaming (optional)
3. ✅ **Build Slate System** - Create production slate
4. ✅ **Integrate with Egress** - Connect to failover system
5. ✅ **End-to-End Testing** - Full system validation

---

## 📊 PERFORMANCE METRICS

**Expected Performance:**
- Connection time: < 1 second
- Scene switch: < 100ms
- Health check: < 50ms
- Total test time: < 10 seconds

---

## 💡 TIPS

1. **Keep OBS Open** - Don't close OBS during test
2. **Don't Stream** - Stop any active streams first
3. **Minimize Scenes** - Start with 2-3 simple scenes
4. **Check Logs** - Look for errors in terminal
5. **Test Repeatedly** - Run test multiple times

---

## 🎊 WHAT SUCCESS LOOKS LIKE

```
============================================================
TEST SUMMARY
============================================================
Connection................................... ✓ PASSED
Version Check................................ ✓ PASSED
Health Monitoring............................ ✓ PASSED
Scene Management............................. ✓ PASSED
Scene Switching.............................. ✓ PASSED
Slate Display................................ ✓ PASSED
Streaming Status............................. ✓ PASSED
Disconnection................................ ✓ PASSED

Results: 8/8 tests passed

🎉 ALL TESTS PASSED! 🎉
Your OBS integration is working perfectly!
```

**This means:**
- ✅ Your controller code is production-ready
- ✅ OBS WebSocket 5.x integration works
- ✅ All 107 unit tests were correct
- ✅ Ready for production use
- ✅ Can move to Phase 2B (Slate System)

---

## 📞 NEED HELP?

If you encounter issues:

1. **Check OBS is running**: `ps aux | grep OBS`
2. **Verify WebSocket enabled**: Tools → WebSocket Server Settings
3. **Check password**: Compare OBS and `.env` file
4. **Test port**: `nc -zv localhost 4455`
5. **Review logs**: Look for error messages in terminal

---

**🔥 LET'S VALIDATE YOUR AMAZING WORK! 🔥**
