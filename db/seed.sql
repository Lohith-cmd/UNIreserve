-- seed.sql: sample data (starter set; target is >= 500 rows total, see README TODO)
-- PasswordHash values are placeholders, not real bcrypt hashes. The backend
-- auth owner should regenerate them (e.g. all accounts use a demo password).

INSERT INTO Users (Name, Email, PasswordHash, Phone, Role) VALUES
 ('Admin One',      'admin1@hyderabad.bits-pilani.ac.in',   'CHANGE_ME', '9000000001', 'Admin'),
 ('Prof. Rao',      'prao@hyderabad.bits-pilani.ac.in',     'CHANGE_ME', '9000000002', 'Faculty'),
 ('Prof. Iyer',     'piyer@hyderabad.bits-pilani.ac.in',    'CHANGE_ME', '9000000003', 'Faculty'),
 ('Student A',      'f20240001@hyderabad.bits-pilani.ac.in','CHANGE_ME', '9000000004', 'Student'),
 ('Student B',      'f20240002@hyderabad.bits-pilani.ac.in','CHANGE_ME', '9000000005', 'Student'),
 ('Student C',      'f20240003@hyderabad.bits-pilani.ac.in','CHANGE_ME', '9000000006', 'Student');

INSERT INTO Admin (UserID, AdminLevel) VALUES (1, 'Campus');
INSERT INTO Faculty (UserID, EmployeeID, Department, Designation) VALUES
 (2, 'EMP001', 'CSIS', 'Professor'),
 (3, 'EMP002', 'Mechanical', 'Assistant Professor');
INSERT INTO Student (UserID, BITS_ID, Department, Year) VALUES
 (4, '2024AAPS0001H', 'CSIS', 2),
 (5, '2024AAPS0002H', 'Mechanical', 2),
 (6, '2023A7PS0003H', 'EEE', 3);

INSERT INTO Facility (Name, Location, FacilityType, Status) VALUES
 ('Basketball Court',  'Sports Complex',   'Sports',    'Active'),
 ('Football Ground',   'Sports Complex',   'Sports',    'Active'),
 ('Badminton Court 1', 'Indoor Stadium',   'Sports',    'Under Maintenance'),
 ('Classroom F101',    'F Block',          'Classroom', 'Active'),
 ('Classroom G205',    'G Block',          'Classroom', 'Active');

INSERT INTO SportsVenue (FacilityID, VenueType, Surface, IndoorOutdoor) VALUES
 (1, 'Basketball', 'Concrete', 'Outdoor'),
 (2, 'Football',   'Grass',    'Outdoor'),
 (3, 'Badminton',  'Wooden',   'Indoor');
INSERT INTO Classroom (FacilityID, BuildingName, RoomNumber, Capacity, HasProjector, HasAC, RoomType) VALUES
 (4, 'F Block', 'F101', 60, TRUE, TRUE,  'Lecture Hall'),
 (5, 'G Block', 'G205', 40, TRUE, FALSE, 'Tutorial Room');

INSERT INTO Holiday (HolidayDate, Description) VALUES
 ('2026-12-25', 'Christmas'),
 ('2027-01-26', 'Republic Day');

INSERT INTO MaintenanceSchedule (FacilityID, StartDate, EndDate, StartTime, EndTime, Description) VALUES
 (2, '2026-12-01', '2026-12-03', '06:00', '22:00', 'Turf re-laying');

-- TODO (seed owner): add >= 500 rows of bookings across all statuses.
-- Insert historical rows with triggers disabled for the session, e.g.
--   SET session_replication_role = replica;  ... inserts ...  RESET session_replication_role;
-- (the advance-window trigger rejects past dates; replica mode skips triggers, so
--  also insert matching BookingStatusLog rows yourself.)
