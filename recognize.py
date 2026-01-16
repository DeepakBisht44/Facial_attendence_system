import face_recognition
import cv2
import pickle
import sys
import json
from datetime import datetime
import csv
from pathlib import Path

# ROOT PATH
ROOT = Path(__file__).resolve().parent.parent
STUDENTS_CSV = ROOT / "students.csv"
ATTENDANCE_CSV = ROOT / "attendance.csv"
RESULT_JSON = ROOT / "result.json"

def recognize_face(encodings_path, threshold=0.35):

    # Load encodings
    try:
        with open(encodings_path, "rb") as f:
            data = pickle.load(f)
        known_encodings = data["encodings"]
        known_ids = data["ids"]
        print(f"Loaded {len(known_encodings)} face encodings")
    except Exception as e:
        print(f"[ERROR] Could not load encodings: {e}")
        return

    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Camera not detected!")
        return

    cap.set(3, 640)
    cap.set(4, 480)

    print("\nCAMERA OPENED - Look at camera (press Q to exit)\n")

    recognized_id = None
    best_dist = 999

    # Recognition loop
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Draw green guide box
        h, w, _ = frame.shape
        cv2.rectangle(frame, (w//4, h//4), (w - w//4, h - h//4), (0,255,0), 2)
        cv2.putText(frame, "Align face in box", (w//4 + 10, h//4 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        # Reduce size for faster recognition
        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        # Detect faces
        boxes = face_recognition.face_locations(rgb, model="hog")

        if len(boxes) > 0:
            # Encode detected faces
            encs = face_recognition.face_encodings(rgb, boxes)

            for enc in encs:
                # Compare with known faces
                distances = face_recognition.face_distance(known_encodings, enc)

                idx = distances.argmin()
                dist = distances[idx]

                # If match found
                if dist < threshold:
                    recognized_id = known_ids[idx]
                    best_dist = dist

                    cv2.putText(frame, f"ID: {recognized_id}", (30, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
                    cv2.putText(frame, f"Match: {(1-dist)*100:.1f}%", (30, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                    break

        cv2.imshow("Recognition", frame)

        # Break if recognized
        if recognized_id is not None:
            cv2.waitKey(2000)  # Show result for 2 seconds
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # If no face recognized
    if recognized_id is None:
        print("[ERROR] No face recognized")
        return

    # Lookup student name
    student_name = "Unknown"
    if STUDENTS_CSV.exists():
        with open(STUDENTS_CSV, "r", encoding="utf-8") as f:
            for row in csv.reader(f):
                if row and row[0] == recognized_id:
                    student_name = row[1]
                    break

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save result.json (for C++ to read)
    with open(RESULT_JSON, "w") as f:
        json.dump({
            "id": recognized_id,
            "name": student_name,
            "time": timestamp,
            "distance": float(best_dist)
        }, f, indent=4)

    # Save attendance in CSV
    with open(ATTENDANCE_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([recognized_id, student_name, timestamp, f"{best_dist:.4f}"])

    print("\n[SUCCESS] Attendance marked!")
    print(f"ID: {recognized_id}")
    print(f"Name: {student_name}")
    print(f"Time: {timestamp}")
    print(f"Distance: {best_dist:.4f}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("[ERROR] Usage: recognize.py <encodings_path> [threshold]")
        sys.exit(1)
    
    enc_path = sys.argv[1]
    threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.35
    recognize_face(enc_path, threshold)