#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <vector>
#include <cstdlib>
using namespace std;

struct Student { string id; string name; };

vector<Student> load_students(const string &path) {
    vector<Student> list;
    ifstream in(path);
    if(!in.is_open()) return list;
    string line;
    while(getline(in,line)) {
        // Skip empty lines
        if(line.empty() || line == "\r" || line == "\n") continue;
        if(line.size()<2) continue;
        
        stringstream ss(line);
        string id,name;
        getline(ss,id,',');
        getline(ss,name,',');
        if(!id.empty()) list.push_back({id,name});
    }
    return list;
}

int main(){
    string python = "py -3.10 ";

    string dataset = "..\\dataset";
    string pyfolder = "..\\python\\";
    string enc_file = pyfolder + "encodings.pkl";
    string students_file = "..\\students.csv";
    string attendance_file = "..\\attendance.csv";
    string result_file = "..\\result.json";

    // Create files if they don't exist
    { ofstream f(students_file, ios::app); }
    { ofstream f(attendance_file, ios::app); }

    while(true){
        cout << "\n===== FRAS MENU =====\n";
        cout << "1) Add student\n";
        cout << "2) Recognize & mark attendance\n";
        cout << "3) Show students\n";
        cout << "4) Show attendance\n";
        cout << "5) Exit\nChoose: ";
        
        int choice;
        if(!(cin >> choice)) break;

        // ADD STUDENT
        if(choice==1){
            string id,name; int samples;
            cout << "Enter ID: "; cin >> id;
            cin.ignore();
            cout << "Enter Name: "; getline(cin,name);
            cout << "Samples (default 20): "; cin >> samples;

            // Run register.py
            string cmd = python + "\"" + pyfolder + "register.py\" \"" 
                        + id + "\" \"" + name + "\" " + to_string(samples);

            system(cmd.c_str());

            // AUTO-ENCODE AFTER REGISTRATION
            string enc_cmd = python + "\"" + pyfolder + "encode_db.py\" \"" 
                            + dataset + "\" \"" + enc_file + "\"";

            cout << "[AUTO] Encoding database...\n";
            system(enc_cmd.c_str());
        }

        // RECOGNIZE & MARK ATTENDANCE
        else if(choice==2){
            // AUTO-ENCODE BEFORE RECOGNITION
            string enc_cmd = python + "\"" + pyfolder + "encode_db.py\" \"" 
                            + dataset + "\" \"" + enc_file + "\"";

            cout << "[AUTO] Encoding latest dataset...\n";
            system(enc_cmd.c_str());

            // Run recognition
            string recog_cmd = python + "\"" + pyfolder + "recognize.py\" \"" 
                               + enc_file + "\" 0.35";
            system(recog_cmd.c_str());

            // Read result.json
            ifstream r(result_file);
            if(!r.is_open()) { 
                cout << "[WARN] No recognition result.\n"; 
                continue; 
            }

            string content,line;
            while(getline(r,line)) content += line;
            r.close();

            // Parse ID from JSON
            size_t p_id = content.find("\"id\"");
            if(p_id == string::npos) {
                cout << "[WARN] No valid ID in result.\n";
                continue;
            }
            size_t q = content.find("\"", p_id+5);
            size_t rpos = content.find("\"", q+1);
            string id = content.substr(q+1, rpos-q-1);

            // Find student name
            vector<Student> list = load_students(students_file);
            string name = "Unknown";
            for(auto &s : list)
                if(s.id == id) name = s.name;

            // Mark attendance (C++ also writes for backup)
            ofstream out(attendance_file, ios::app);
            out << id << "," << name << "\n";
            out.close();

            cout << "[SUCCESS] Attendance marked for " << name << endl;
        }

        // SHOW STUDENTS
        else if(choice == 3){
            auto list = load_students(students_file);
            cout << "\n--- Students List ---\n";
            for(auto &s : list) cout<<s.id<<" | "<<s.name<<"\n";
        }

        // SHOW ATTENDANCE
        else if(choice == 4){
            ifstream in(attendance_file);
            string line;
            cout << "\n--- Attendance Records ---\n";
            while(getline(in,line)) cout<<line<<"\n";
        }

        // EXIT
        else if(choice == 5){
            cout << "Exiting...\n";
            break;
        }

        else {
            cout << "Invalid choice.\n";
        }
    }

    return 0;
}