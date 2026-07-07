# Guptrix Developer Guide

Welcome to Guptrix! This guide is written for completely new developers. Whether you are adding a feature, fixing a bug, or pushing a new release to the Google Play Store, everything you need to know is right here.

---

## 1. What is Guptrix?

Guptrix is a highly secure, end-to-end encrypted notes application. 
Because true privacy requires notes to be encrypted *before* they are sent to the server, Guptrix is built with three main parts:

1. **Frontend (`Guptrix_FE`)**: A Next.js web application. This handles the UI, the editor, and the encryption logic. 
2. **Backend (`Guptrix_BE`)**: An Express.js & MongoDB server. This just blindly stores encrypted text. It cannot read user notes.
3. **Android App (`android-app`)**: A native Android wrapper. It loads the Frontend via a `WebView`, but also has deep native integration for offline caching, downloads, and intents.

---

## 2. Where is Everything? (Folder Structure)

If you need to change something, here is where you look:

### Android App (`android-app/`)
*   **`app/src/main/java/com/guptrix/app/`**: Contains the Kotlin code for the Android app.
    *   `ui/`: Contains all the Fragments and Activities (e.g., `MainActivity.kt`, `NotesFragment.kt`, `SettingsFragment.kt`).
    *   `database/`: Contains the Room Database setup (`AppDatabase.kt`, `NoteDao.kt`) used for **offline caching**.
    *   `WebViewManager.kt`: The bridge between the native Android app and the Next.js frontend.
*   **`app/src/main/res/`**: Contains the native Android UI designs.
    *   `layout/`: XML files defining the screen UI (e.g., `activity_main.xml`, `fragment_settings.xml`).
    *   `values/themes.xml`: Contains the Material 3 color palette.

### The Editor 
**"Why does the editor live in the web frontend instead of native Android?"**
Because encryption logic is complex. By building the editor in Next.js (`Guptrix_FE`), both the website users and the Android app users share the exact same encryption algorithms. The Android App simply loads the editor via a `WebView` inside `HomeFragment.kt`.

---

## 3. How to Compile and Run the Android App

Before you run the app, ensure your environment is set up:
*   Install Android Studio.
*   Ensure `JAVA_HOME` is set to Java 21 (or compatible version).

### Running a Debug Build (Local Testing)
To test your changes directly on your phone or emulator via command line:

```bash
# 1. Navigate to the Android folder
cd ~/testing/app/Guptrix/android-app

# 2. Set necessary environment variables
export ANDROID_HOME=$HOME/Android/Sdk
export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/build-tools/37.0.0:$PATH
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk

# 3. Compile the debug APK
./gradlew assembleDebug

# 4. Install it on your connected device (ensure ADB is connected)
adb install -r app/build/outputs/apk/debug/app-arm64-v8a-debug.apk

# 5. Launch the app
adb shell am start -n com.guptrix.app/.ui.MainActivity
```

---

## 4. How to Build and Publish to the Google Play Store

Google Play requires a **signed Release AAB** (Android App Bundle).

### Step 1: Compile the Release Build
```bash
cd ~/testing/app/Guptrix/android-app

# Run the Gradle task to build the release App Bundle and APK
./gradlew bundleRelease assembleRelease
```

### Step 2: Sign the Build
Android requires apps to be cryptographically signed to prove they haven't been tampered with.

```bash
# Sign the APK using the debug keystore (For local testing only)
apksigner sign --ks ~/.android/debug.keystore --ks-pass pass:android --key-pass pass:android --ks-key-alias androiddebugkey app/build/outputs/apk/release/app-universal-release-unsigned.apk

# For actual Google Play Store Production:
# You must use your PRODUCTION keystore (e.g., guptrix-release-key.jks)
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 -keystore /path/to/guptrix-release-key.jks app/build/outputs/bundle/release/app-release.aab key_alias
```

### Step 3: Upload to Google Play Console
1. Go to the [Google Play Console](https://play.google.com/console).
2. Select **Guptrix**.
3. Go to **Production** -> **Create new release**.
4. Upload the signed `.aab` file located at: `app/build/outputs/bundle/release/app-release.aab`.
5. Fill in the Release Notes.
6. Click **Save** -> **Review Release** -> **Start rollout to Production**.

---

## 5. Play Console Submission Fixes & GitHub Releases

If you encounter errors when submitting to the Google Play Console, these are the common issues and the exact steps used to fix them during the v1.0.2 release.

### Issue 1: "You must complete the advertising ID declaration..."
Android 13 (API 33) and above requires you to declare an advertising ID permission if any SDK requests it.
**Fix:** We added this specific permission to `android-app/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="com.google.android.gms.permission.AD_ID" />
```

### Issue 2: "Must target at least API level 35"
Google Play constantly updates its minimum security requirements. If you get this error, you must bump the SDK targets.
**Fix:** Edit `android-app/app/build.gradle.kts` and update both `compileSdk` and `targetSdk`:
```kotlin
compileSdk = 35
defaultConfig {
    targetSdk = 35
    versionCode = 3      // ALWAYS increment this number on every new upload!
    versionName = "1.0.2" // Increment the visual version
}
```

### Issue 3: "Version code X has already been used."
Even if you delete a draft upload, Google Play remembers the `versionCode`.
**Fix:** Simply increment the `versionCode` in `build.gradle.kts` by 1 and rebuild the bundle.

### Issue 4: "All uploaded bundles must be signed."
The Play Console rejects raw `.aab` files built directly out of `./gradlew bundleRelease`. It must be cryptographically signed with your developer key.
**Fix (Generate & Sign):**
```bash
# 1. Generate your personal Release Keystore (You only do this ONCE)
keytool -genkey -v -keystore guptrix-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias guptrix-key -dname "CN=Guptrix Developer, OU=Guptrix App, O=Guptrix, L=World, S=World, C=US" -storepass guptrixpass -keypass guptrixpass

# 2. Sign the bundle using jarsigner
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 -keystore guptrix-release-key.jks app/build/outputs/bundle/release/app-release.aab guptrix-key -storepass guptrixpass -keypass guptrixpass
```

### Creating a GitHub Release via CLI
When a new version is ready, you should push a formal release to GitHub using the `gh` command-line tool, attaching both the signed APK for users and the debug APK for testers.

```bash
# Example to create a v1.0.2 release and upload binaries
gh release create v1.0.2 \
    android-app/app/build/outputs/apk/release/app-release-signed.apk \
    android-app/app/build/outputs/apk/debug/app-universal-debug.apk \
    --title "v1.0.2" \
    --notes "Guptrix v1.0.2 - Initial Release!"
```

---

## 5. Troubleshooting & ADB Commands

If the app crashes, you need to view the logs to see what went wrong.

**View Crash Logs:**
```bash
adb logcat -d | grep -E "AndroidRuntime|FATAL|Exception" | tail -n 50
```

**Clear App Data (Simulate fresh install):**
```bash
adb shell pm clear com.guptrix.app
```

**Force Offline Mode on Emulator:**
```bash
adb shell svc wifi disable
adb shell svc data disable
```
