import pandas as pd
from pathlib import Path

# 1. Locate and load the Student Excel file
excel_candidates = list(Path(".").glob("Year and Disp wise List*.xlsx")) + list(Path(".").glob("*.xlsx"))
if not excel_candidates:
    raise FileNotFoundError("Could not find the Student Excel (.xlsx) file in the project root!")
excel_file = str(excel_candidates[0])
print(f"Loading student data from: {excel_file}")

df1 = pd.read_excel(excel_file, sheet_name="11 FEB")
df2 = pd.read_excel(excel_file, sheet_name="12 FEB")
df_all = pd.concat([df1, df2], ignore_index=True)

# Filter admission years 2020-2024 (excludes the single 2018 outlier row)
df_filtered = df_all[df_all["Year"].between(2020, 2024)].copy()

disp_map = {
    "A1": "CHE", "A2": "CE", "A3": "EEE", "A4": "ME", "A5": "PHARM",
    "A7": "CS", "A8": "EEE", "AA": "EEE", "AD": "MATH",
    "B1": "BIO", "B2": "CHEM", "B3": "ECON", "B4": "MATH", "B5": "PHY",
}
df_filtered["Dept"] = df_filtered["Disp"].map(disp_map)
df_filtered["Email_lower"] = df_filtered["Email"].str.strip().str.lower()
df_filtered["Name_clean"] = df_filtered["Name"].str.replace(r"\s+", " ", regex=True).str.strip()
df_filtered["Campus_ID_clean"] = df_filtered["Campus ID"].str.strip()

# 2. Admin Data (UserID 1 for primary test compatibility + UserIDs 901..910 across 3 clearance tiers)
admins = [
    (1,   "Admin One",                        "admin1@hyderabad.bits-pilani.ac.in",           "9000000001", "Level 3 - Campus"),
    (901, "Associate Dean Administration",    "assocdean.admin@hyderabad.bits-pilani.ac.in",  "9000000901", "Level 3 - Campus"),
    (902, "Chief Warden",                     "chiefwarden@hyderabad.bits-pilani.ac.in",      "9000000902", "Level 3 - Campus"),
    (903, "Estate Officer",                   "estate.officer@hyderabad.bits-pilani.ac.in",   "9000000903", "Level 3 - Campus"),
    (904, "Timetable & Classroom Coordinator","timetable.admin@hyderabad.bits-pilani.ac.in",  "9000000904", "Level 2 - Zone"),
    (905, "Sports & SAC Officer",             "sports.officer@hyderabad.bits-pilani.ac.in",   "9000000905", "Level 2 - Zone"),
    (906, "Auditorium & Events Coordinator",  "events.admin@hyderabad.bits-pilani.ac.in",     "9000000906", "Level 2 - Zone"),
    (907, "Academic Block Caretaker",         "ab.caretaker@hyderabad.bits-pilani.ac.in",     "9000000907", "Level 1 - Operational"),
    (908, "New Academic Block Caretaker",     "nab.caretaker@hyderabad.bits-pilani.ac.in",    "9000000908", "Level 1 - Operational"),
    (909, "SAC Caretaker",                    "sac.caretaker@hyderabad.bits-pilani.ac.in",    "9000000909", "Level 1 - Operational"),
    (910, "IT & Lab Systems Admin",           "labs.admin@hyderabad.bits-pilani.ac.in",       "9000000910", "Level 1 - Operational"),
]

# 3. Faculty Data (UserIDs 2..104: 103 BITS Pilani Hyderabad Professors)
faculty_list = [
    (2,  'EMP001', 'Prof. Paresh Saxena',               'psaxena@hyderabad.bits-pilani.ac.in',           '04066303591', 'CS',    'Associate Professor & HoD'),
    (3,  'EMP002', 'Prof. Sabareesh Geetha Rajasekharan','sabareesh@hyderabad.bits-pilani.ac.in',        '04066303655', 'ME',    'Professor & HoD'),
    (4,  'EMP003', 'Prof. Chittaranjan Hota',           'hota@hyderabad.bits-pilani.ac.in',              '04066303504', 'CS',    'Senior Professor'),
    (5,  'EMP004', 'Prof. G. Geethakumari',             'geetha@hyderabad.bits-pilani.ac.in',            '04066303560', 'CS',    'Professor'),
    (6,  'EMP005', 'Prof. Navneet Goyal',               'goyal@hyderabad.bits-pilani.ac.in',             '04066303561', 'CS',    'Professor'),
    (7,  'EMP006', 'Prof. Aruna Malapati',              'arunam@hyderabad.bits-pilani.ac.in',            '04066303562', 'CS',    'Associate Professor'),
    (8,  'EMP007', 'Prof. Subhrakanta Panda',           'spanda@hyderabad.bits-pilani.ac.in',            '04066303563', 'CS',    'Associate Professor'),
    (9,  'EMP008', 'Prof. Manik Gupta',                 'manik@hyderabad.bits-pilani.ac.in',             '04066303564', 'CS',    'Associate Professor'),
    (10, 'EMP009', 'Prof. Dipanjan Chakraborty',        'dipanjan@hyderabad.bits-pilani.ac.in',          '04066303565', 'CS',    'Associate Professor'),
    (11, 'EMP010', 'Prof. Raghunath Reddy Madireddy',   'raghunath@hyderabad.bits-pilani.ac.in',         '04066303767', 'CS',    'Associate Professor'),
    (12, 'EMP011', 'Prof. Barsha Mitra',                'barsha.mitra@hyderabad.bits-pilani.ac.in',      '04066303566', 'CS',    'Associate Professor'),
    (13, 'EMP012', 'Prof. Abhijit Das',                 'abhijit.das@hyderabad.bits-pilani.ac.in',       '04066303567', 'CS',    'Assistant Professor'),
    (14, 'EMP013', 'Prof. Nikumani Choudhury',          'nikumani@hyderabad.bits-pilani.ac.in',          '04066303568', 'CS',    'Assistant Professor'),
    (15, 'EMP014', 'Prof. Jabez Christopher',           'jabez@hyderabad.bits-pilani.ac.in',             '04066303569', 'CS',    'Assistant Professor'),
    (16, 'EMP015', 'Prof. Prajna Upadhyay',             'prajna.u@hyderabad.bits-pilani.ac.in',          '04066303670', 'CS',    'Assistant Professor'),
    (17, 'EMP016', 'Prof. Sk Aziz Ali',                 'aziz.ali@hyderabad.bits-pilani.ac.in',          '04066303671', 'CS',    'Assistant Professor'),
    (18, 'EMP017', 'Prof. Aritra Mukherjee',            'aritra.mukherjee@hyderabad.bits-pilani.ac.in',  '04066303672', 'CS',    'Assistant Professor'),
    (19, 'EMP018', 'Prof. Joyjit Mukherjee',            'joyjit.m@hyderabad.bits-pilani.ac.in',          '04066303673', 'CS',    'Assistant Professor'),
    (20, 'EMP019', 'Prof. Akanksha Rathore',            'akanksha.r@hyderabad.bits-pilani.ac.in',        '04066303674', 'CS',    'Assistant Professor'),
    (21, 'EMP020', 'Prof. Jay Kamlesh Dave',            'jay.dave@hyderabad.bits-pilani.ac.in',          '04066303675', 'CS',    'Assistant Professor'),
    (22, 'EMP021', 'Prof. Harish V. Dixit',             'harish.dixit@hyderabad.bits-pilani.ac.in',      '04066303650', 'EEE',   'Professor & HoD'),
    (23, 'EMP022', 'Prof. Sanket Goel',                 'sgoel@hyderabad.bits-pilani.ac.in',             '04066303610', 'EEE',   'Professor'),
    (24, 'EMP023', 'Prof. Subhendu Kumar Sahoo',        'sahoo@hyderabad.bits-pilani.ac.in',             '04066303611', 'EEE',   'Professor'),
    (25, 'EMP024', 'Prof. Prasant Kumar Pattnaik',      'pkpattnaik@hyderabad.bits-pilani.ac.in',        '04066303612', 'EEE',   'Associate Professor'),
    (26, 'EMP025', 'Prof. Syed Ershad Ahmed',           'ershad@hyderabad.bits-pilani.ac.in',            '04066303613', 'EEE',   'Associate Professor'),
    (27, 'EMP026', 'Prof. Mithun Mondal',               'mithun@hyderabad.bits-pilani.ac.in',            '04066303614', 'EEE',   'Associate Professor'),
    (28, 'EMP027', 'Prof. Parikshit Sahatiya',          'parikshit@hyderabad.bits-pilani.ac.in',         '04066303615', 'EEE',   'Associate Professor'),
    (29, 'EMP028', 'Prof. Anakhi Hazarika',             'anakhi@hyderabad.bits-pilani.ac.in',            '04066303616', 'EEE',   'Assistant Professor'),
    (30, 'EMP029', 'Prof. Sk Masum Nawaz',              'nawaz.masum@hyderabad.bits-pilani.ac.in',       '04066303786', 'EEE',   'Assistant Professor'),
    (31, 'EMP030', 'Prof. V. Vamsi Krishna',            'vamsi.krishna@hyderabad.bits-pilani.ac.in',     '04066303618', 'EEE',   'Assistant Professor'),
    (32, 'EMP031', 'Prof. Sandip S. Deshmukh',          'ssd@hyderabad.bits-pilani.ac.in',               '04066303531', 'ME',    'Professor'),
    (33, 'EMP032', 'Prof. Jeevan Jaidi',                'jaidi@hyderabad.bits-pilani.ac.in',             '04066303532', 'ME',    'Professor'),
    (34, 'EMP033', 'Prof. Satish Kumar Dubey',          'skdubey@hyderabad.bits-pilani.ac.in',           '04066303533', 'ME',    'Associate Professor'),
    (35, 'EMP034', 'Prof. Jalaiah Nandanavanam',        'jalaiah@hyderabad.bits-pilani.ac.in',           '04066303534', 'ME',    'Associate Professor'),
    (36, 'EMP035', 'Prof. Santanu Prasad Datta',        'spdatta@hyderabad.bits-pilani.ac.in',           '04066303535', 'ME',    'Associate Professor'),
    (37, 'EMP036', 'Prof. Brajesh Kumar Panigrahi',     'brajesh@hyderabad.bits-pilani.ac.in',           '04066303536', 'ME',    'Assistant Professor'),
    (38, 'EMP037', 'Prof. Kundan Kumar Singh',          'ksingh@hyderabad.bits-pilani.ac.in',            '04066303731', 'ME',    'Assistant Professor'),
    (39, 'EMP038', 'Prof. Pritam Bari',                 'pritam.bari@hyderabad.bits-pilani.ac.in',       '04066303732', 'ME',    'Assistant Professor'),
    (40, 'EMP039', 'Prof. Smruti Parimita',             'smruti.p@hyderabad.bits-pilani.ac.in',          '04066303733', 'ME',    'Assistant Professor'),
    (41, 'EMP040', 'Prof. Abhishek Sarkar',             'abhishek.sarkar@hyderabad.bits-pilani.ac.in',   '04066303734', 'ME',    'Assistant Professor'),
    (42, 'EMP041', 'Prof. V. Vinayaka Ram',             'vinayak@hyderabad.bits-pilani.ac.in',           '04066303580', 'CE',    'Professor'),
    (43, 'EMP042', 'Prof. Prasanta Kumar Sahu',         'pksahu@hyderabad.bits-pilani.ac.in',            '04066303581', 'CE',    'Professor'),
    (44, 'EMP043', 'Prof. Sridhar Raju',                'sridhar.raju@hyderabad.bits-pilani.ac.in',      '04066303682', 'CE',    'Associate Professor'),
    (45, 'EMP044', 'Prof. Murari R. R. Varma',          'murari@hyderabad.bits-pilani.ac.in',            '04066303584', 'CE',    'Associate Professor'),
    (46, 'EMP045', 'Prof. Arkamitra Kar',               'arkamitra.kar@hyderabad.bits-pilani.ac.in',     '04066303679', 'CE',    'Associate Professor'),
    (47, 'EMP046', 'Prof. Anasua Guharay',              'anasua@hyderabad.bits-pilani.ac.in',            '04066303585', 'CE',    'Associate Professor'),
    (48, 'EMP047', 'Prof. Bandhan Bandhu Majumdar',     'majumdar@hyderabad.bits-pilani.ac.in',          '04066303587', 'CE',    'Associate Professor'),
    (49, 'EMP048', 'Prof. K. Rajitha',                  'rajitha@hyderabad.bits-pilani.ac.in',           '04066303588', 'CE',    'Assistant Professor'),
    (50, 'EMP049', 'Prof. Bahurudeen A.',               'bahurudeen@hyderabad.bits-pilani.ac.in',        '04066303589', 'CE',    'Associate Professor'),
    (51, 'EMP050', 'Prof. Raghuram Ammavajjala',        'raghuram.a@hyderabad.bits-pilani.ac.in',        '04066303590', 'CE',    'Assistant Professor'),
    (52, 'EMP051', 'Prof. I. Sreedhar',                 'isreedhar@hyderabad.bits-pilani.ac.in',         '04066303512', 'CHE',   'Professor & HoD'),
    (53, 'EMP052', 'Prof. Srikanta Dinda',              'srikantadinda@hyderabad.bits-pilani.ac.in',     '04066303586', 'CHE',   'Professor'),
    (54, 'EMP053', 'Prof. Ramesh Adusumalli',           'ramesh.babu@hyderabad.bits-pilani.ac.in',       '04066303554', 'CHE',   'Professor'),
    (55, 'EMP054', 'Prof. Balaji Krishnamurthy',        'balaji@hyderabad.bits-pilani.ac.in',            '04066303552', 'CHE',   'Professor'),
    (56, 'EMP055', 'Prof. Srinivas Appari',             'srinivas.appari@hyderabad.bits-pilani.ac.in',   '04066303555', 'CHE',   'Associate Professor'),
    (57, 'EMP056', 'Prof. Arnab Dutta',                 'arnabdutta@hyderabad.bits-pilani.ac.in',        '04066303758', 'CHE',   'Assistant Professor'),
    (58, 'EMP057', 'Prof. Afkham Mir',                  'afkham.mir@hyderabad.bits-pilani.ac.in',        '04066303759', 'CHE',   'Assistant Professor'),
    (59, 'EMP058', 'Prof. Ramendra Kishor Pal',         'ramendra.pal@hyderabad.bits-pilani.ac.in',      '04066303760', 'CHE',   'Assistant Professor'),
    (60, 'EMP059', 'Prof. Arti Dhar',                   'artidhar@hyderabad.bits-pilani.ac.in',          '04066303647', 'PHARM', 'Professor & HoD'),
    (61, 'EMP060', 'Prof. P. Yogeeswari',               'pyogeeswari@hyderabad.bits-pilani.ac.in',       '04066303505', 'PHARM', 'Senior Professor'),
    (62, 'EMP061', 'Prof. Punna Rao Ravi',              'rpunnarao@hyderabad.bits-pilani.ac.in',         '04066303540', 'PHARM', 'Professor'),
    (63, 'EMP062', 'Prof. Balaram Ghosh',               'balaram@hyderabad.bits-pilani.ac.in',           '04066303541', 'PHARM', 'Professor'),
    (64, 'EMP063', 'Prof. Akash Chaurasiya',            'akashc@hyderabad.bits-pilani.ac.in',            '04066303542', 'PHARM', 'Associate Professor'),
    (65, 'EMP064', 'Prof. Onkar Prakash Kulkarni',      'onkar@hyderabad.bits-pilani.ac.in',             '04066303543', 'PHARM', 'Associate Professor'),
    (66, 'EMP065', 'Prof. Nirmal Jayabalan',            'nirmalj@hyderabad.bits-pilani.ac.in',           '04066303544', 'PHARM', 'Assistant Professor'),
    (67, 'EMP066', 'Prof. Ch. Mohan Rao',               'mohanrao@hyderabad.bits-pilani.ac.in',          '04066303775', 'BIO',   'Distinguished Professor & HoD'),
    (68, 'EMP067', 'Prof. Vidya Rajesh',                'vidya@hyderabad.bits-pilani.ac.in',             '04066303545', 'BIO',   'Professor'),
    (69, 'EMP068', 'Prof. Kumar Pranav Narayan',        'pranav@hyderabad.bits-pilani.ac.in',            '04066303546', 'BIO',   'Professor'),
    (70, 'EMP069', 'Prof. P. Sankar Ganesh',            'sankarganesh@hyderabad.bits-pilani.ac.in',      '04066303547', 'BIO',   'Associate Professor'),
    (71, 'EMP070', 'Prof. G. Sundar',                   'sundarg@hyderabad.bits-pilani.ac.in',           '04066303501', 'CHEM',  'Senior Professor'),
    (72, 'EMP071', 'Prof. Anupam Bhattacharya',         'anupam@hyderabad.bits-pilani.ac.in',            '04066303522', 'CHEM',  'Professor'),
    (73, 'EMP072', 'Prof. N. Rajesh',                   'nrajesh@hyderabad.bits-pilani.ac.in',           '04066303523', 'CHEM',  'Professor'),
    (74, 'EMP073', 'Prof. K. V. G. Chandra Sekhar',     'kvgc@hyderabad.bits-pilani.ac.in',              '04066303524', 'CHEM',  'Professor'),
    (75, 'EMP074', 'Prof. Durba Roy',                   'durbaroy@hyderabad.bits-pilani.ac.in',          '04066303525', 'CHEM',  'Associate Professor'),
    (76, 'EMP075', 'Prof. Arijit Mukherjee',            'arijit.m@hyderabad.bits-pilani.ac.in',          '04066303526', 'CHEM',  'Assistant Professor'),
    (77, 'EMP076', 'Prof. Suryoday Prodhan',            'suryoday@hyderabad.bits-pilani.ac.in',          '04066303527', 'CHEM',  'Assistant Professor'),
    (78, 'EMP077', 'Prof. Rishi Kumar',                 'rishikumar@hyderabad.bits-pilani.ac.in',        '04066303570', 'ECON',  'Associate Professor & HoD'),
    (79, 'EMP078', 'Prof. Swati Alok',                  'swati@hyderabad.bits-pilani.ac.in',             '04066303571', 'ECON',  'Associate Professor'),
    (80, 'EMP079', 'Prof. Nivedita Sinha',              'nivedita@hyderabad.bits-pilani.ac.in',          '04066303572', 'ECON',  'Associate Professor'),
    (81, 'EMP080', 'Prof. Thota Nagaraju',              'nagaraju@hyderabad.bits-pilani.ac.in',          '04066303573', 'ECON',  'Associate Professor'),
    (82, 'EMP081', 'Prof. Sudatta Banerjee',            'sudatta@hyderabad.bits-pilani.ac.in',           '04066303574', 'ECON',  'Associate Professor'),
    (83, 'EMP082', 'Prof. Bheemeshwar Reddy A.',        'bheem@hyderabad.bits-pilani.ac.in',             '04066303575', 'ECON',  'Assistant Professor'),
    (84, 'EMP083', 'Prof. Sunny Kumar Singh',           'sunnysingh@hyderabad.bits-pilani.ac.in',        '04066303576', 'ECON',  'Assistant Professor'),
    (85, 'EMP084', 'Prof. Pradyumn Kumar Sahoo',        'pksahoo@hyderabad.bits-pilani.ac.in',           '04066303515', 'MATH',  'Professor & HoD'),
    (86, 'EMP085', 'Prof. Bivudutta Mishra',            'bivudutta@hyderabad.bits-pilani.ac.in',         '04066303516', 'MATH',  'Professor'),
    (87, 'EMP086', 'Prof. Dipak Kumar Satpathi',        'dipak@hyderabad.bits-pilani.ac.in',             '04066303517', 'MATH',  'Associate Professor'),
    (88, 'EMP087', 'Prof. N. Anil',                     'anil@hyderabad.bits-pilani.ac.in',              '04066303694', 'MATH',  'Associate Professor'),
    (89, 'EMP088', 'Prof. T. S. L. Radhika',            'radhika@hyderabad.bits-pilani.ac.in',           '04066303518', 'MATH',  'Associate Professor'),
    (90, 'EMP089', 'Prof. Jaganmohan Jonnalagadda',     'jagan@hyderabad.bits-pilani.ac.in',             '04066303519', 'MATH',  'Associate Professor'),
    (91, 'EMP090', 'Prof. Manish Kumar',                'manish.kumar@hyderabad.bits-pilani.ac.in',      '04066303520', 'MATH',  'Assistant Professor'),
    (92, 'EMP091', 'Prof. Santanu Koley',               'santanu@hyderabad.bits-pilani.ac.in',           '04066303521', 'MATH',  'Assistant Professor'),
    (93, 'EMP092', 'Prof. Nijjwal Karak',               'nijjwal@hyderabad.bits-pilani.ac.in',           '04066303695', 'MATH',  'Assistant Professor'),
    (94, 'EMP093', 'Prof. Kannan Ramaswamy',            'kannan@hyderabad.bits-pilani.ac.in',            '04066303550', 'PHY',   'Professor & HoD'),
    (95, 'EMP094', 'Prof. V. Satya Narayana Murthy',    'vsnmurthy@hyderabad.bits-pilani.ac.in',         '04066303551', 'PHY',   'Professor'),
    (96, 'EMP095', 'Prof. B. Harihara Venkataraman',    'harihara@hyderabad.bits-pilani.ac.in',          '04066303553', 'PHY',   'Associate Professor'),
    (97, 'EMP096', 'Prof. Aravinda N. Raghavan',        'aravinda@hyderabad.bits-pilani.ac.in',          '04066303556', 'PHY',   'Associate Professor'),
    (98, 'EMP097', 'Prof. Rahul Nigam',                 'rahul.nigam@hyderabad.bits-pilani.ac.in',       '04066303557', 'PHY',   'Associate Professor'),
    (99, 'EMP098', 'Prof. Sashideep Gutti',             'sashideep@hyderabad.bits-pilani.ac.in',         '04066303558', 'PHY',   'Associate Professor'),
    (100,'EMP099', 'Prof. Prasant Kumar Samantray',     'prasant.samantray@hyderabad.bits-pilani.ac.in', '04066303609', 'PHY',   'Assistant Professor'),
    (101,'EMP100', 'Prof. Shilpaa Anand',               'shilpaa@hyderabad.bits-pilani.ac.in',           '04066303610', 'HSS',   'Associate Professor & HoD'),
    (102,'EMP101', 'Prof. Lavanya Suresh',              'lavanya@hyderabad.bits-pilani.ac.in',           '04066303620', 'HSS',   'Associate Professor'),
    (103,'EMP102', 'Prof. Suchismita Satpathy',         'suchismita@hyderabad.bits-pilani.ac.in',        '04066303621', 'HSS',   'Associate Professor'),
    (104,'EMP103', 'Prof. Biswanath Dash',              'biswanath@hyderabad.bits-pilani.ac.in',         '04066303622', 'HSS',   'Associate Professor'),
]

# 4. Facilities (4-digit FacilityIDs: Classrooms 1001..1156, Sports 2001..2014, Other 3001..3002)
facilities = []
classrooms = []
sports_venues = []
other_facilities = []

fac_id = 1001

# F Block: F101..F109, F201..F209 (Location: AB)
for rm_num in range(1, 10):
    room = f"F10{rm_num}"
    if room in ("F102", "F105"):
        cap, rtype = 350, "Large Lecture Hall"
    elif room in ("F107", "F108", "F109"):
        cap, rtype = 60, "Classroom"
    else:
        cap, rtype = 200, "Lecture Hall"
    facilities.append((fac_id, f"Classroom {room}", "AB", "Classroom", "Active"))
    classrooms.append((fac_id, "F Block", room, cap, "TRUE", "TRUE", rtype))
    fac_id += 1

for rm_num in range(1, 10):
    room = f"F20{rm_num}"
    facilities.append((fac_id, f"Classroom {room}", "AB", "Classroom", "Active"))
    classrooms.append((fac_id, "F Block", room, 75, "TRUE", "TRUE", "Classroom"))
    fac_id += 1

# G Block: G101..G114, G201..G212 (Location: AB)
for rm_num in range(1, 15):
    room = f"G1{rm_num:02d}"
    facilities.append((fac_id, f"Classroom {room}", "AB", "Classroom", "Active"))
    classrooms.append((fac_id, "G Block", room, 45, "TRUE", "TRUE", "Tutorial Room"))
    fac_id += 1

for rm_num in range(1, 13):
    room = f"G2{rm_num:02d}"
    facilities.append((fac_id, f"Classroom {room}", "AB", "Classroom", "Active"))
    classrooms.append((fac_id, "G Block", room, 45, "TRUE", "TRUE", "Tutorial Room"))
    fac_id += 1

# New Acad Blocks H, I, J, K: floors 1..3, rooms 01..08 (Location: NAB)
for blk in ("H", "I", "J", "K"):
    for fl in (1, 2, 3):
        for rm_num in range(1, 9):
            room = f"{blk}{fl}{rm_num:02d}"
            facilities.append((fac_id, f"Classroom {room}", "NAB", "Classroom", "Active"))
            classrooms.append((fac_id, f"{blk} Block", room, 80, "TRUE", "TRUE", "Classroom"))
            fac_id += 1

# NAB Labs
nab_labs = [
    ("H209", "H Block", "Communications Lab"),
    ("I010", "I Block", "Digital Lab"),
    ("I012", "I Block", "Digital Signals Lab"),
    ("I109", "I Block", "IT Lab"),
    ("I311", "I Block", "Robotics Lab"),
    ("J010", "J Block", "IOT Lab"),
    ("J011", "J Block", "FPGA Lab"),
]
for room, blk, lab_name in nab_labs:
    facilities.append((fac_id, f"{room} - {lab_name}", "NAB", "Classroom", "Active"))
    classrooms.append((fac_id, blk, room, 60, "TRUE", "TRUE", lab_name))
    fac_id += 1

# D Block Labs (Location: AB)
d_labs = [
    ("D110", "CS Lab"), ("D111", "CS Lab"), ("D112", "CS Lab"),
    ("D210", "EG Lab"), ("D211", "EG Lab"), ("D212", "EG Lab"),
    ("D311", "CS Lab"), ("D312", "CS Lab"), ("D313", "CS Lab"),
]
for room, lab_name in d_labs:
    facilities.append((fac_id, f"{room} - {lab_name}", "AB", "Classroom", "Active"))
    classrooms.append((fac_id, "D Block", room, 60, "TRUE", "TRUE", lab_name))
    fac_id += 1

# Sports Facilities: 2001..2014 (NSAC = Near SAC, SAC = Inside SAC)
sports_data = [
    (2001, "TennisCourt 1",        "NSAC", "Tennis",       "Synthetic", "Outdoor"),
    (2002, "TennisCourt 2",        "NSAC", "Tennis",       "Synthetic", "Outdoor"),
    (2003, "BasketballCourt 1",    "NSAC", "Basketball",   "Concrete",  "Outdoor"),
    (2004, "BasketballCourt 2",    "NSAC", "Basketball",   "Concrete",  "Outdoor"),
    (2005, "Table Tennis Table 1", "SAC",  "Table Tennis", "Wooden",    "Indoor"),
    (2006, "Table Tennis Table 2", "SAC",  "Table Tennis", "Wooden",    "Indoor"),
    (2007, "Table Tennis Table 3", "SAC",  "Table Tennis", "Wooden",    "Indoor"),
    (2008, "Badminton Court 1",    "SAC",  "Badminton",    "Wooden",    "Indoor"),
    (2009, "Badminton Court 2",    "SAC",  "Badminton",    "Wooden",    "Indoor"),
    (2010, "Dance Room",           "SAC",  "Dance",        "Wooden",    "Indoor"),
    (2011, "Squash Room",          "SAC",  "Squash",       "Wooden",    "Indoor"),
    (2012, "Pool Table 1",         "SAC",  "Pool",         "Felt",      "Indoor"),
    (2013, "Pool Table 2",         "SAC",  "Pool",         "Felt",      "Indoor"),
    (2014, "Pool Table 3",         "SAC",  "Pool",         "Felt",      "Indoor"),
]
for sid, sname, sloc, vtype, surf, inout in sports_data:
    facilities.append((sid, sname, sloc, "Sports", "Active"))
    sports_venues.append((sid, vtype, surf, inout))

# Other Facilities: 3001..3002 (Auditorium & Open Amphitheatre in AB)
# Stored with FacilityType 'Other' (not Classroom) so the weekday-evening classroom rule does not apply.
facilities.append((3001, "Auditorium",        "AB", "Other", "Active"))
other_facilities.append((3001, "Auditorium",   1000, "TRUE",  "TRUE",  "Indoor"))
facilities.append((3002, "Open Amphitheatre", "AB", "Other", "Active"))
other_facilities.append((3002, "Amphitheatre", 1500, "FALSE", "FALSE", "Outdoor"))

# 5. Holidays from BITS Academic Calendar 2026-27
holidays = [
    ("2026-08-15", "Independence Day"),
    ("2026-08-26", "Milad-un-Nabi"),
    ("2026-08-28", "Raksha Bandhan"),
    ("2026-09-04", "Janmashtami"),
    ("2026-09-14", "Ganesh Chaturthi"),
    ("2026-10-02", "Mahatma Gandhi Jayanti"),
    ("2026-10-20", "Dussehra"),
    ("2026-11-08", "Deepavali"),
    ("2026-11-09", "Govardhan Puja"),
    ("2026-11-24", "Guru Nanak Jayanti"),
    ("2026-12-25", "Christmas"),
    ("2027-01-26", "Republic Day"),
]

# 6. Maintenance Schedules (4 rows)
maint_rows = [
    (2001, "2026-12-01", "2026-12-03", "06:00", "22:00", "Tennis court synthetic resurfacing"),
    (1002, "2026-12-05", "2026-12-06", "08:00", "18:00", "F102 Laser projector & audio calibration"),
    (2008, "2026-12-10", "2026-12-11", "06:00", "14:00", "Badminton wooden floor polishing"),
    (3001, "2026-12-15", "2026-12-16", "09:00", "17:00", "Auditorium HVAC & stage lighting servicing"),
]

# 7. 25 Bookings + Corresponding BookingStatusLog Entries (using historical dates so live tests don't collide)
stu_ids = [int(df_filtered.iloc[i]["ID"]) for i in range(25)]
bookings = [
    (1,  stu_ids[0],  2001, "2026-10-12", "17:00", "18:00", "Completed", "Evening tennis practice",             905),
    (2,  stu_ids[1],  2003, "2026-10-12", "18:00", "19:00", "Completed", "Inter-hostel basketball practice",   905),
    (3,  2,           1001, "2026-10-13", "18:00", "20:00", "Completed", "CS extra doubt-clearing session",    904),
    (4,  3,           1002, "2026-10-14", "18:00", "21:00", "Completed", "Mechanical guest lecture",           904),
    (5,  stu_ids[2],  2005, "2026-10-15", "16:00", "17:00", "Completed", "Table tennis match",                 909),
    (6,  stu_ids[3],  2008, "2026-10-16", "19:00", "20:00", "Completed", "Badminton club trials",              905),
    (7,  stu_ids[4],  2008, "2026-10-16", "19:00", "20:00", "Rejected",  "Casual badminton game",              905),
    (8,  4,           1045, "2026-10-17", "10:00", "12:00", "Completed", "Weekend research colloquium",        904),
    (9,  stu_ids[5],  2010, "2026-10-18", "17:00", "18:00", "Completed", "Dance club choreography rehearsal",  909),
    (10, stu_ids[6],  2011, "2026-10-19", "07:00", "08:00", "Cancelled", "Morning squash session",             stu_ids[6]),
    (11, 22,          1141, "2026-10-21", "18:00", "20:00", "Completed", "Communications lab makeup session",  910),
    (12, stu_ids[7],  2012, "2026-10-22", "18:00", "19:00", "Completed", "8-ball pool tournament qualifier",   909),
    (13, 32,          3001, "2026-10-24", "14:00", "17:00", "Completed", "Department symposium in Auditorium", 906),
    (14, stu_ids[8],  3002, "2026-10-25", "18:30", "19:30", "Completed", "Music club acoustic night",          906),
    (15, stu_ids[9],  1019, "2026-10-26", "18:00", "19:00", "Rejected",  "Coding club peer mentoring",         904),
    (16, 52,          1005, "2026-10-27", "18:00", "20:30", "Completed", "Chemical Engg quiz review",          904),
    (17, stu_ids[10], 2002, "2026-10-28", "06:30", "07:30", "Completed", "Morning tennis drills",              905),
    (18, stu_ids[11], 2004, "2026-10-29", "17:30", "18:30", "Cancelled", "Basketball 3v3 warmup",              stu_ids[11]),
    (19, 78,          1033, "2026-10-30", "18:00", "20:00", "Completed", "Economics seminar prep",             904),
    (20, stu_ids[12], 2009, "2026-11-01", "16:00", "17:00", "Confirmed", "Badminton doubles practice",         905),
    (21, stu_ids[13], 2006, "2026-11-02", "18:00", "19:00", "Confirmed", "TT ladder match",                    909),
    (22, 85,          1070, "2026-11-03", "18:00", "20:00", "Confirmed", "Mathematics Olympiad training",      904),
    (23, stu_ids[14], 2013, "2026-11-04", "19:00", "20:00", "Pending",   "Evening pool practice",              stu_ids[14]),
    (24, stu_ids[15], 1148, "2026-11-05", "18:00", "19:00", "Pending",   "Competitive programming practice",   stu_ids[15]),
    (25, 94,          1095, "2026-11-05", "18:30", "20:30", "Confirmed", "Quantum physics tutorial",           904),
]

# Format SQL blocks
adm_users = [f"  ({u}, '{n}', '{em}', 'Bits@{u}', '{ph}', 'Admin')" for u, n, em, ph, lvl in admins]
adm_sub   = [f"  ({u}, '{lvl}')" for u, n, em, ph, lvl in admins]

fac_users = [f"  ({u}, '{n}', '{em}', 'Bits@{u}', '{ph}', 'Faculty')" for u, emp, n, em, ph, d, des in faculty_list]
fac_sub   = [f"  ({u}, '{emp}', '{d}', '{des}')" for u, emp, n, em, ph, d, des in faculty_list]

stu_users, stu_sub = [], []
for row in df_filtered.itertuples():
    uid = int(row.ID)
    name = row.Name_clean.replace("'", "''")
    email = row.Email_lower.replace("'", "''")
    bits_id = row.Campus_ID_clean.replace("'", "''")
    stu_users.append(f"  ({uid}, '{name}', '{email}', 'Bits@{uid}', NULL, 'Student')")
    stu_sub.append(f"  ({uid}, '{bits_id}', '{row.Dept}', {int(row.Year)})")

fac_rows_sql   = [f"  ({fid}, '{nm}', '{loc}', '{ft}', '{st}')" for fid, nm, loc, ft, st in facilities]
class_rows_sql = [f"  ({fid}, '{blk}', '{rm}', {cap}, {proj}, {ac}, '{rt}')" for fid, blk, rm, cap, proj, ac, rt in classrooms]
sport_rows_sql = [f"  ({fid}, '{vt}', '{sf}', '{io}')" for fid, vt, sf, io in sports_venues]
other_rows_sql = [f"  ({fid}, '{cat}', {cap}, {proj}, {ac}, '{io}')" for fid, cat, cap, proj, ac, io in other_facilities]
hol_rows_sql   = [f"  ('{dt}', '{desc}')" for dt, desc in holidays]
maint_rows_sql = [f"  ({fid}, '{sd}', '{ed}', '{st}', '{et}', '{desc}')" for fid, sd, ed, st, et, desc in maint_rows]

book_rows_sql = []
log_rows_sql  = []
for bid, uid, fid, bdate, st, et, status, purp, actor in bookings:
    book_rows_sql.append(f"  ({bid}, {uid}, {fid}, '{bdate}', '{st}', '{et}', '{status}', '{purp}')")
    log_rows_sql.append(f"  ({bid}, NULL, 'Pending', {uid})")
    if status == "Confirmed":
        log_rows_sql.append(f"  ({bid}, 'Pending', 'Confirmed', {actor})")
    elif status == "Completed":
        log_rows_sql.append(f"  ({bid}, 'Pending', 'Confirmed', {actor})")
        log_rows_sql.append(f"  ({bid}, 'Confirmed', 'Completed', {actor})")
    elif status in ("Rejected", "Cancelled"):
        log_rows_sql.append(f"  ({bid}, 'Pending', '{status}', {actor})")

seed_sql = f"""-- seed.sql: Campus Facility Booking System (BITS Pilani Hyderabad)
-- Includes 11 Admins, 103 Faculty, 4,045 Students, 172 Facilities (4-digit IDs),
-- 12 Holidays, 4 Maintenance Windows, and 25 Bookings with Audit Logs.

-- 1. Admins (UserID 1 + 901..910)
INSERT INTO Users (UserID, Name, Email, PasswordHash, Phone, Role) VALUES
{",\n".join(adm_users)};

INSERT INTO Admin (UserID, AdminLevel) VALUES
{",\n".join(adm_sub)};

-- 2. Faculty (UserIDs 2..104)
INSERT INTO Users (UserID, Name, Email, PasswordHash, Phone, Role) VALUES
{",\n".join(fac_users)};

INSERT INTO Faculty (UserID, EmployeeID, Department, Designation) VALUES
{",\n".join(fac_sub)};

-- 3. Students (4,045 rows from 2020-2024 batches)
INSERT INTO Users (UserID, Name, Email, PasswordHash, Phone, Role) VALUES
{",\n".join(stu_users)};

INSERT INTO Student (UserID, BITS_ID, Department, Year) VALUES
{",\n".join(stu_sub)};

SELECT setval(pg_get_serial_sequence('Users', 'userid'), (SELECT MAX(UserID) FROM Users));

-- 4. Facilities (Classrooms 1001..1156, Sports 2001..2014, Other 3001..3002)
INSERT INTO Facility (FacilityID, Name, Location, FacilityType, Status) VALUES
{",\n".join(fac_rows_sql)};

INSERT INTO Classroom (FacilityID, BuildingName, RoomNumber, Capacity, HasProjector, HasAC, RoomType) VALUES
{",\n".join(class_rows_sql)};

INSERT INTO SportsVenue (FacilityID, VenueType, Surface, IndoorOutdoor) VALUES
{",\n".join(sport_rows_sql)};

INSERT INTO OtherFacility (FacilityID, VenueCategory, Capacity, HasProjector, HasAC, IndoorOutdoor) VALUES
{",\n".join(other_rows_sql)};

SELECT setval(pg_get_serial_sequence('Facility', 'facilityid'), (SELECT MAX(FacilityID) FROM Facility));

-- 5. Academic Calendar Holidays
INSERT INTO Holiday (HolidayDate, Description) VALUES
{",\n".join(hol_rows_sql)};

-- 6. Maintenance Schedules
INSERT INTO MaintenanceSchedule (FacilityID, StartDate, EndDate, StartTime, EndTime, Description) VALUES
{",\n".join(maint_rows_sql)};

-- 7. Seed Bookings & Audit Logs (Bypass triggers for historical dates)
SET session_replication_role = replica;

INSERT INTO Booking (BookingID, UserID, FacilityID, BookingDate, StartTime, EndTime, Status, Purpose) VALUES
{",\n".join(book_rows_sql)};

INSERT INTO BookingStatusLog (BookingID, OldStatus, NewStatus, ChangedByUserID) VALUES
{",\n".join(log_rows_sql)};

RESET session_replication_role;

SELECT setval(pg_get_serial_sequence('Booking', 'bookingid'), (SELECT MAX(BookingID) FROM Booking));
SELECT setval(pg_get_serial_sequence('BookingStatusLog', 'logid'), (SELECT MAX(LogID) FROM BookingStatusLog));
"""

Path("db/seed.sql").write_text(seed_sql, encoding="utf-8")
print(f"Successfully generated db/seed.sql with {len(stu_users)} students, {len(faculty_list)} faculty, {len(admins)} admins, and {len(facilities)} facilities!")

# 8. Update db/tests.sql so all 45 automated checks use the new 11-digit Student IDs and 4-digit FacilityIDs
u_s1, u_s2, u_s3 = stu_ids[0], stu_ids[1], stu_ids[2]
tests_path = Path("db/tests.sql")
t_sql = tests_path.read_text(encoding="utf-8")

# Ensure clean replacement from original tests.sql
t_sql = t_sql.replace(
    "CREATE FUNCTION pg_temp.ins(p_user INT, p_fac INT, p_date TEXT, p_start TEXT, p_end TEXT)",
    "CREATE FUNCTION pg_temp.ins(p_user BIGINT, p_fac INT, p_date TEXT, p_start TEXT, p_end TEXT)"
)
t_sql = t_sql.replace(
    "INSERT INTO Holiday (HolidayDate, Description) SELECT hol, 'test holiday' FROM t_dates\nON CONFLICT DO NOTHING;",
    "INSERT INTO Holiday (HolidayDate, Description) SELECT hol, 'test holiday' FROM t_dates\nON CONFLICT DO NOTHING;\nUPDATE Facility SET Status = 'Under Maintenance' WHERE FacilityID = 2003;"
)
t_sql = t_sql.replace(
    "SELECT pg_temp.expect('C student year out-of-range rejected',\n    $q$WITH u AS (INSERT INTO Users (Name, Email, PasswordHash, Role) VALUES ('T', 'ty6@x.com', 'x', 'Student') RETURNING UserID)\n       INSERT INTO Student SELECT UserID, 'TESTID00000X1', 'CSIS', 2025 FROM u$q$, false);\nSELECT pg_temp.expect('C student year 2022 accepted',\n    $q$WITH u AS (INSERT INTO Users (Name, Email, PasswordHash, Role) VALUES ('T', 'ty3@x.com', 'x', 'Student') RETURNING UserID)\n       INSERT INTO Student SELECT UserID, 'TESTID00000X2', 'CSIS', 2022 FROM u$q$, true);",
    "SELECT pg_temp.expect('C student year 2018 rejected',\n    $q$WITH u AS (INSERT INTO Users (Name, Email, PasswordHash, Role) VALUES ('T', 'ty2018@x.com', 'x', 'Student') RETURNING UserID)\n       INSERT INTO Student SELECT UserID, 'TESTID00000X1', 'CS', 2018 FROM u$q$, false);\nSELECT pg_temp.expect('C student year 2024 accepted',\n    $q$WITH u AS (INSERT INTO Users (Name, Email, PasswordHash, Role) VALUES ('T', 'ty2024@x.com', 'x', 'Student') RETURNING UserID)\n       INSERT INTO Student SELECT UserID, 'TESTID00000X2', 'CS', 2024 FROM u$q$, true);"
)

# Replace facility IDs (1->2001, 2->2002, 3->2003, 4->1001, 5->1002) and student UserIDs (4,5,6 -> u_s1,u_s2,u_s3)
replacements = [
    (f"pg_temp.ins(4, 1,", f"pg_temp.ins({u_s1}, 2001,"),
    (f"pg_temp.ins(4, 3,", f"pg_temp.ins({u_s1}, 2003,"),
    (f"pg_temp.ins(4, 4,", f"pg_temp.ins({u_s1}, 1001,"),
    (f"pg_temp.ins(5, 1,", f"pg_temp.ins({u_s2}, 2001,"),
    (f"pg_temp.ins({u_s1}, 1,", f"pg_temp.ins({u_s1}, 2001,"),
    (f"pg_temp.ins({u_s1}, 3,", f"pg_temp.ins({u_s1}, 2003,"),
    (f"pg_temp.ins({u_s1}, 4,", f"pg_temp.ins({u_s1}, 1001,"),
    (f"pg_temp.ins({u_s2}, 1,", f"pg_temp.ins({u_s2}, 2001,"),
    ("pg_temp.ins(2, 1,", "pg_temp.ins(2, 2001,"),
    ("pg_temp.ins(2, 4,", "pg_temp.ins(2, 1001,"),
    ("pg_temp.ins(1, 4,", "pg_temp.ins(1, 1001,"),
    ("INSERT INTO MaintenanceSchedule (FacilityID,", "INSERT INTO MaintenanceSchedule (FacilityID,"),
    ("VALUES (1, (SELECT wd FROM t_dates),", "VALUES (2001, (SELECT wd FROM t_dates),"),
    ("WHERE UserID = 4", f"WHERE UserID = {u_s1}"),
    ("VALUES (4, 1, d", f"VALUES ({u_s1}, 2001, d"),
    ("VALUES (5, 1, d", f"VALUES ({u_s2}, 2001, d"),
    ("VALUES (6, 1, d", f"VALUES ({u_s3}, 2001, d"),
    ("VALUES (4, 2, d", f"VALUES ({u_s1}, 2002, d"),
    ("VALUES (5, 2, CURRENT_DATE", f"VALUES ({u_s2}, 2002, CURRENT_DATE"),
    (f"VALUES ({u_s1}, 1, d", f"VALUES ({u_s1}, 2001, d"),
    (f"VALUES ({u_s2}, 1, d", f"VALUES ({u_s2}, 2001, d"),
    (f"VALUES ({u_s3}, 1, d", f"VALUES ({u_s3}, 2001, d"),
    (f"VALUES ({u_s1}, 2, d", f"VALUES ({u_s1}, 2002, d"),
    (f"VALUES ({u_s2}, 2, CURRENT_DATE", f"VALUES ({u_s2}, 2002, CURRENT_DATE"),
    ("VALUES (2, 1, d", "VALUES (2, 2001, d"),
    ("format('SELECT cancel_booking(%s, 6)', b_wrong)", f"format('SELECT cancel_booking(%s, {u_s3})', b_wrong)"),
    ("format('SELECT cancel_booking(%s, 5)', b_cancel)", f"format('SELECT cancel_booking(%s, {u_s2})', b_cancel)"),
    ("format('SELECT cancel_booking(%s, 5)', b_wrong)", f"format('SELECT cancel_booking(%s, {u_s2})', b_wrong)"),
    ("WHERE FacilityID = 3) = 'Under Maintenance'", "WHERE FacilityID = 2003) = 'Under Maintenance'"),
    ("WHERE FacilityID = 1) = 'Available'", "WHERE FacilityID = 2001) = 'Available'"),
    ("WHERE FacilityID = 1)", "WHERE FacilityID = 2001)"),
]
for old, new in replacements:
    t_sql = t_sql.replace(old, new)

tests_path.write_text(t_sql, encoding="utf-8")
print("Updated db/tests.sql successfully!")

