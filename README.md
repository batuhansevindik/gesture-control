# 🖐️ Gesture Control System (OpenCV + MediaPipe)

A real-time computer vision system that allows controlling system functions using hand gestures via webcam.

## 🚀 Features

* ✖️ **Cross Gesture Detection**

  * Cross your hands to trigger an action window
  * Within 2 seconds, show open palms to confirm
  * Locks the screen if confirmed

* 🖐️ **Palm Confirmation Mechanism**

  * Prevents accidental triggers
  * Requires deliberate gesture (open palms)

* 🔊 **Volume Control with Hand Motion**

  * 4-finger horizontal gesture
  * Move hand up → Volume Up
  * Move hand down → Volume Down
  * Highly sensitive and responsive

* 🎯 **Real-Time Tracking**

  * Uses MediaPipe hand tracking
  * Works with a standard webcam

---

## 🧠 How It Works

### 🔒 Screen Lock Flow

1. Perform a **cross gesture** with both hands
2. System enters a **2-second confirmation window**
3. Show **both open palms**
4. Screen locks

If no confirmation is given → action is cancelled.

---

### 🔊 Volume Control Flow

1. Show **4 fingers (thumb ignored)**
2. Keep hand **horizontal**
3. Move:

   * ↑ Up → increase volume
   * ↓ Down → decrease volume

---

## 🛠️ Technologies Used

* Python 3
* OpenCV
* MediaPipe
* Linux system commands (`pactl`, `loginctl`)

---

## 📦 Installation

```bash
sudo apt update
sudo apt install python3-pip
pip install opencv-python mediapipe
```

---

## ▶️ Usage

```bash
python cross_lock.py
```

Press **`q`** to exit.

---

## ⚠️ Notes

* Designed for Linux environments (tested on Ubuntu)
* Uses:

  * `loginctl lock-session` → screen lock
  * `pactl` → volume control
* Performance depends on lighting and camera quality

---

## 📁 Project Structure

```
gesture-control/
│
├── cross_lock.py          # Main system
├── lock_watcher.sh        # Background lock watcher
├── start_cross_lock.sh    # Startup script
├── launch_watcher.sh      # Auto-launch handler
├── test_hand.py           # Testing utilities
├── fist_lock.py           # Alternative gesture logic
└── .gitignore
```

---

## 🔥 Future Improvements

* Gesture customization system
* GUI interface
* Cross-platform support (Windows / macOS)
* Machine learning-based gesture classification

---

## 👤 Author

Batuhan Sevindik
Computer Engineering Student

---

## ⭐️ If you like the project

Give it a ⭐️ on GitHub and improve it further.
