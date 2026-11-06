-- tests.sql: exercises every trigger, function and CHECK/UNIQUE constraint.
-- Run against a freshly seeded database (see README). Everything runs inside one
-- transaction that is rolled back at the end, so no data is changed.
-- Dates are computed relative to today so the tests do not go stale.
-- Seed assumptions: users 2,3 = Faculty; 4,5,6 = Student; facilities 1,2 = Sports (Active),
-- 3 = Sports (Under Maintenance), 4,5 = Classroom.

BEGIN;

CREATE TEMP TABLE t_results (label TEXT, passed BOOLEAN);
CREATE TEMP TABLE t_dates AS
SELECT (SELECT MIN(d)::date FROM generate_series(CURRENT_DATE + 1, CURRENT_DATE + 6, INTERVAL '1 day') d
         WHERE EXTRACT(DOW FROM d) BETWEEN 1 AND 5) AS wd,    -- a weekday
       (SELECT MIN(d)::date FROM generate_series(CURRENT_DATE + 1, CURRENT_DATE + 6, INTERVAL '1 day') d
         WHERE EXTRACT(DOW FROM d) IN (0, 6))        AS we,    -- a weekend day
       (SELECT MAX(d)::date FROM generate_series(CURRENT_DATE + 1, CURRENT_DATE + 6, INTERVAL '1 day') d
         WHERE EXTRACT(DOW FROM d) BETWEEN 1 AND 5) AS hol;    -- another weekday, made a holiday below

INSERT INTO Holiday (HolidayDate, Description) SELECT hol, 'test holiday' FROM t_dates
ON CONFLICT DO NOTHING;

-- Runs sql; records PASS if it succeeded (should_pass) or failed (NOT should_pass).
CREATE FUNCTION pg_temp.expect(p_label TEXT, p_sql TEXT, p_should_pass BOOLEAN) RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE ok BOOLEAN;
BEGIN
    BEGIN
        EXECUTE p_sql;
        ok := p_should_pass;
    EXCEPTION WHEN OTHERS THEN
        ok := NOT p_should_pass;
    END;
    INSERT INTO t_results VALUES (p_label, ok);
END $$;

CREATE FUNCTION pg_temp.ins(p_user INT, p_fac INT, p_date TEXT, p_start TEXT, p_end TEXT) RETURNS TEXT
LANGUAGE sql AS $$
    SELECT format('INSERT INTO Booking (UserID, FacilityID, BookingDate, StartTime, EndTime) VALUES (%s, %s, %s, %L, %L)',
                  p_user, p_fac, p_date, p_start, p_end);
$$;

-- ---------- Trigger 1: duration limits ----------
SELECT pg_temp.expect('T1 student 2h sports rejected',        pg_temp.ins(4,1,'(SELECT we FROM t_dates)','10:00','12:00'), false);
SELECT pg_temp.expect('T1 student 1h sports accepted',        pg_temp.ins(4,1,'(SELECT we FROM t_dates)','10:00','11:00'), true);
SELECT pg_temp.expect('T1 student 2h classroom rejected',     pg_temp.ins(4,4,'(SELECT we FROM t_dates)','09:00','11:00'), false);
SELECT pg_temp.expect('T1 faculty 90min sports rejected',     pg_temp.ins(2,1,'(SELECT we FROM t_dates)','12:00','13:30'), false);
SELECT pg_temp.expect('T1 faculty 3h classroom accepted',     pg_temp.ins(2,4,'(SELECT we FROM t_dates)','09:00','12:00'), true);
SELECT pg_temp.expect('T1 faculty 3.5h classroom rejected',   pg_temp.ins(2,4,'(SELECT we FROM t_dates)','13:00','16:30'), false);
SELECT pg_temp.expect('T1 30min minimum accepted',            pg_temp.ins(4,1,'(SELECT we FROM t_dates)','16:00','16:30'), true);

-- ---------- Trigger 2: availability ----------
SELECT pg_temp.expect('T2 classroom weekday 10:00 rejected',  pg_temp.ins(2,4,'(SELECT wd FROM t_dates)','10:00','11:00'), false);
SELECT pg_temp.expect('T2 classroom weekday 18:00 accepted',  pg_temp.ins(2,4,'(SELECT wd FROM t_dates)','18:00','19:00'), true);
SELECT pg_temp.expect('T2 classroom weekday after 22:00 rejected', pg_temp.ins(2,5,'(SELECT wd FROM t_dates)','21:30','22:30'), false);
SELECT pg_temp.expect('T2 classroom weekend 07:00 rejected',  pg_temp.ins(2,5,'(SELECT we FROM t_dates)','07:00','08:00'), false);
SELECT pg_temp.expect('T2 classroom weekend 21:30-22:30 rejected', pg_temp.ins(2,5,'(SELECT we FROM t_dates)','21:30','22:30'), false);
SELECT pg_temp.expect('T2 classroom holiday 10:00 accepted',  pg_temp.ins(2,5,'(SELECT hol FROM t_dates)','10:00','11:00'), true);
SELECT pg_temp.expect('T2 sports before 06:00 rejected',      pg_temp.ins(4,2,'(SELECT wd FROM t_dates)','05:30','06:00'), false);
SELECT pg_temp.expect('T2 sports after 22:00 rejected',       pg_temp.ins(4,2,'(SELECT wd FROM t_dates)','21:30','22:30'), false);
SELECT pg_temp.expect('T2 facility Under Maintenance rejected', pg_temp.ins(4,3,'(SELECT wd FROM t_dates)','10:00','11:00'), false);

INSERT INTO MaintenanceSchedule (FacilityID, StartDate, EndDate, StartTime, EndTime, Description)
SELECT 5, we, we, '10:00', '12:00', 'test window' FROM t_dates;
SELECT pg_temp.expect('T2 overlaps maintenance window rejected', pg_temp.ins(2,5,'(SELECT we FROM t_dates)','10:30','11:30'), false);
SELECT pg_temp.expect('T2 outside maintenance window accepted',  pg_temp.ins(2,5,'(SELECT we FROM t_dates)','14:00','15:00'), true);

-- ---------- Trigger 3: advance-booking window ----------
SELECT pg_temp.expect('T3 student 7 days ahead accepted',  pg_temp.ins(5,2,'CURRENT_DATE + 7','10:00','11:00'), true);
SELECT pg_temp.expect('T3 student 8 days ahead rejected',  pg_temp.ins(5,2,'CURRENT_DATE + 8','10:00','11:00'), false);
SELECT pg_temp.expect('T3 faculty 14 days ahead accepted', pg_temp.ins(3,2,'CURRENT_DATE + 14','10:00','11:00'), true);
SELECT pg_temp.expect('T3 faculty 15 days ahead rejected', pg_temp.ins(3,2,'CURRENT_DATE + 15','10:00','11:00'), false);
SELECT pg_temp.expect('T3 past date rejected',             pg_temp.ins(5,2,'CURRENT_DATE - 1','10:00','11:00'), false);

-- ---------- CHECK / UNIQUE constraints ----------
SELECT pg_temp.expect('C end = start rejected',       pg_temp.ins(5,2,'CURRENT_DATE + 2','10:00','10:00'), false);
SELECT pg_temp.expect('C off 30-min grid rejected',   pg_temp.ins(5,2,'CURRENT_DATE + 2','10:15','11:00'), false);
SELECT pg_temp.expect('C duplicate email rejected',
    $q$INSERT INTO Users (Name, Email, PasswordHash, Role) VALUES ('Dup', 'admin1@hyderabad.bits-pilani.ac.in', 'x', 'Student')$q$, false);
SELECT pg_temp.expect('C student year 6 rejected',
    $q$WITH u AS (INSERT INTO Users (Name, Email, PasswordHash, Role) VALUES ('T', 'ty6@x.com', 'x', 'Student') RETURNING UserID)
       INSERT INTO Student SELECT UserID, 'TESTID00000X1', 'CSIS', 6 FROM u$q$, false);
SELECT pg_temp.expect('C student year 3 accepted',
    $q$WITH u AS (INSERT INTO Users (Name, Email, PasswordHash, Role) VALUES ('T', 'ty3@x.com', 'x', 'Student') RETURNING UserID)
       INSERT INTO Student SELECT UserID, 'TESTID00000X2', 'CSIS', 3 FROM u$q$, true);
SELECT pg_temp.expect('C classroom capacity 0 rejected',
    $q$WITH f AS (INSERT INTO Facility (Name, FacilityType) VALUES ('Tmp', 'Classroom') RETURNING FacilityID)
       INSERT INTO Classroom (FacilityID, BuildingName, RoomNumber, Capacity) SELECT FacilityID, 'B', '1', 0 FROM f$q$, false);
SELECT pg_temp.expect('C holiday duplicate date rejected',
    $q$INSERT INTO Holiday (HolidayDate, Description) SELECT hol, 'dup' FROM t_dates$q$, false);
SELECT pg_temp.expect('C delete user with bookings restricted',
    $q$DELETE FROM Users WHERE UserID = 4$q$, false);

-- ---------- Trigger 4 + 5: auto-reject and audit log; cancel_booking ----------
DO $$
DECLARE
    d DATE := (SELECT wd FROM t_dates);
    b4 INT; b5 INT; b6 INT; b_other INT; b_cancel INT; b_wrong INT;
    n INT; s TEXT;
BEGIN
    -- three pending requests: identical slot (4,5) and partially overlapping slot (6)
    INSERT INTO Booking (UserID, FacilityID, BookingDate, StartTime, EndTime) VALUES (4, 1, d, '14:00', '15:00') RETURNING BookingID INTO b4;
    INSERT INTO Booking (UserID, FacilityID, BookingDate, StartTime, EndTime) VALUES (5, 1, d, '14:00', '15:00') RETURNING BookingID INTO b5;
    INSERT INTO Booking (UserID, FacilityID, BookingDate, StartTime, EndTime) VALUES (6, 1, d, '14:30', '15:30') RETURNING BookingID INTO b6;
    -- same user, different facility, overlapping time
    INSERT INTO Booking (UserID, FacilityID, BookingDate, StartTime, EndTime) VALUES (4, 2, d, '14:30', '15:30') RETURNING BookingID INTO b_other;

    PERFORM set_config('app.current_user_id', '1', true);   -- admin confirms
    UPDATE Booking SET Status = 'Confirmed' WHERE BookingID = b4;

    SELECT Status::text INTO s FROM Booking WHERE BookingID = b5;
    INSERT INTO t_results VALUES ('T4 identical-slot pending auto-rejected', s = 'Rejected');
    SELECT Status::text INTO s FROM Booking WHERE BookingID = b6;
    INSERT INTO t_results VALUES ('T4 overlapping pending auto-rejected', s = 'Rejected');
    SELECT Status::text INTO s FROM Booking WHERE BookingID = b_other;
    INSERT INTO t_results VALUES ('T4 other facility untouched', s = 'Pending');

    PERFORM pg_temp.expect('T4 user overlapping confirmed booking blocks confirm',
        format('UPDATE Booking SET Status = ''Confirmed'' WHERE BookingID = %s', b_other), false);

    SELECT COUNT(*) INTO n FROM BookingStatusLog WHERE BookingID = b4;
    INSERT INTO t_results VALUES ('T5 confirmed booking has insert + confirm log rows', n = 2);
    SELECT COUNT(*) INTO n FROM BookingStatusLog
     WHERE BookingID = b5 AND OldStatus = 'Pending' AND NewStatus = 'Rejected' AND ChangedByUserID = 1;
    INSERT INTO t_results VALUES ('T5 auto-reject logged with acting admin', n = 1);

    -- cancel_booking
    INSERT INTO Booking (UserID, FacilityID, BookingDate, StartTime, EndTime) VALUES (5, 2, CURRENT_DATE + 5, '10:00', '11:00') RETURNING BookingID INTO b_cancel;
    INSERT INTO Booking (UserID, FacilityID, BookingDate, StartTime, EndTime) VALUES (5, 2, CURRENT_DATE + 5, '12:00', '13:00') RETURNING BookingID INTO b_wrong;
    PERFORM pg_temp.expect('cancel_booking by wrong user rejected',
        format('SELECT cancel_booking(%s, 6)', b_wrong), false);
    PERFORM pg_temp.expect('cancel_booking by owner accepted',
        format('SELECT cancel_booking(%s, 5)', b_cancel), true);
    SELECT Status::text INTO s FROM Booking WHERE BookingID = b_cancel;
    INSERT INTO t_results VALUES ('cancel_booking sets Cancelled', s = 'Cancelled');
    PERFORM pg_temp.expect('cancel_booking on Cancelled booking rejected',
        format('SELECT cancel_booking(%s, 5)', b_cancel), false);

    -- 2-hour rule: needs a slot starting within the next 2 hours, only possible 05:00-20:00
    IF LOCALTIME BETWEEN TIME '05:00' AND TIME '20:00' THEN
        INSERT INTO Booking (UserID, FacilityID, BookingDate, StartTime, EndTime)
        VALUES (5, 2, CURRENT_DATE, (DATE_TRUNC('hour', LOCALTIMESTAMP) + INTERVAL '1 hour')::time,
                                    (DATE_TRUNC('hour', LOCALTIMESTAMP) + INTERVAL '2 hour')::time)
        RETURNING BookingID INTO b_wrong;
        PERFORM pg_temp.expect('cancel_booking inside 2h window rejected',
            format('SELECT cancel_booking(%s, 5)', b_wrong), false);
    ELSE
        RAISE NOTICE 'SKIPPED 2-hour cancellation test (only runs between 05:00 and 20:00 server time)';
    END IF;
END $$;

-- ---------- Views ----------
SELECT pg_temp.expect('view facility_availability_view queryable', 'SELECT * FROM facility_availability_view', true);
SELECT pg_temp.expect('view booking_summary_view queryable',       'SELECT * FROM booking_summary_view', true);

-- ---------- Report ----------
SELECT CASE WHEN passed THEN 'PASS' ELSE 'FAIL' END AS result, label FROM t_results ORDER BY passed, label;
SELECT COUNT(*) FILTER (WHERE passed) AS passed, COUNT(*) FILTER (WHERE NOT passed) AS failed FROM t_results;

ROLLBACK;
