import cv2, sys, csv
from pathlib import Path
import face_recognition

# Absolute paths
ROOT = Path(__file__).resolve().parent.parent
DATASET = ROOT / "dataset"
STUDENTS_CSV = ROOT / "students.csv"

def register(student_id, student_name, samples=20):

    # Ensure dataset folder exists
    DATASET.mkdir(exist_ok=True)

    # Student folder
    student_dir = DATASET / student_id
    student_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Saving images to: {student_dir}")

    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Camera not detected!")
        return 1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    count = 0

    # Capture loop
    while count < samples:
        ret, frame = cap.read()
        if not ret:
            continue

        # Convert to RGB and shrink for fast detection
        rgb = frame[:, :, ::-1]
        small = cv2.resize(rgb, (0, 0), fx=0.5, fy=0.5)

        # Detect faces
        boxes = face_recognition.face_locations(small, model="hog")

        for (top, right, bottom, left) in boxes:

            # Scale back the box (because we used 0.5 size)
            top *= 2; right *= 2; bottom *= 2; left *= 2

            # Extract face
            face_img = frame[top:bottom, left:right]

            # Skip if face area is invalid
            if face_img.size == 0:
                continue

            # Save face image
            img_path = student_dir / f"{student_id}_{count+1}.jpg"
            cv2.imwrite(str(img_path), face_img)

            count += 1
            print(f"[OK] Captured {count}/{samples}")

        cv2.imshow("Register - Press Q to stop", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Check if student already exists
    existing_ids = set()
    if STUDENTS_CSV.exists():
        with open(STUDENTS_CSV, "r", encoding="utf-8") as f:
            existing_ids = {row[0] for row in csv.reader(f) if row}

    # Append student to students.csv (only if new)
    if student_id not in existing_ids:
        with open(STUDENTS_CSV, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([student_id, student_name])
        print(f"[INFO] Student {student_id} added to database")
    else:
        print(f"[WARN] Student {student_id} already exists - updated images only")

    print(f"[DONE] Registration complete for {student_name} (ID: {student_id})")

    return 0


if __name__ == "__main__":
    sid = sys.argv[1]
    name = sys.argv[2]
    samples = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    register(sid, name, samples)