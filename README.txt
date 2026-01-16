FinalFRAS - Face Recognition Attendance System (Clean build)
-----------------------------------------------------------
Structure (root):
  - dataset/               (store student image folders here: dataset/<id>/*.jpg)
  - students.csv           (project root)
  - attendance.csv         (project root)
  - python/                (python scripts and encodings.pkl here)
  - cpp/                   (main.cpp here)

How to run (Windows, after unzip):
  1) Open PowerShell and navigate to FinalFRAS/cpp
  2) Compile main.cpp with MinGW (optional) or run Python scripts directly:
     g++ main.cpp -o fras.exe -Wl,-subsystem,console
  3) Run the program:
     ./fras.exe
  4) Menu:
     1 -> Add student (captures images via webcam and auto-encodes)
     2 -> Recognize & mark attendance (auto-encodes before recognition)
     3 -> Show students
     4 -> Show attendance
     5 -> Exit

Notes:
  - Python scripts use face_recognition and OpenCV (install via pip)
  - Threshold set to 0.35 (strict). Edit recognize.py to change.
  - Encodings saved to python/encodings.pkl
