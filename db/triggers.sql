-- triggers.sql: all 5 triggers (run after schema.sql and procedures.sql)
--
-- Backend convention: inside each transaction that changes a booking, run
--   SELECT set_config('app.current_user_id', '<acting user id>', true);
-- so the audit log records who made the change (NULL if unset).

-- Drop guards so this file can be re-run on its own during development.
DROP TRIGGER IF EXISTS trg_booking_duration               ON Booking;
DROP TRIGGER IF EXISTS trg_booking_classroom_availability ON Booking;
DROP TRIGGER IF EXISTS trg_booking_advance_window         ON Booking;
DROP TRIGGER IF EXISTS trg_booking_auto_reject            ON Booking;
DROP TRIGGER IF EXISTS trg_booking_audit_log              ON Booking;

-- ===============================================================
-- 1. BEFORE INSERT: duration limits
--    Student: max 1h any facility. Faculty: max 1h sports, 3h classroom or other.
--    Admin: no cap. Minimum for everyone: 30 min.
-- ===============================================================
CREATE OR REPLACE FUNCTION fn_booking_duration() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
DECLARE
    v_role  user_role;
    v_type  facility_type;
    v_mins  NUMERIC := EXTRACT(EPOCH FROM (NEW.EndTime - NEW.StartTime)) / 60;
BEGIN
    SELECT Role INTO v_role FROM Users WHERE UserID = NEW.UserID;
    SELECT FacilityType INTO v_type FROM Facility WHERE FacilityID = NEW.FacilityID;

    IF v_mins < 30 THEN
        RAISE EXCEPTION 'Minimum booking duration is 30 minutes';
    END IF;

    IF v_role = 'Student' AND v_mins > 60 THEN
        RAISE EXCEPTION 'Students may book at most 1 hour per booking';
    ELSIF v_role = 'Faculty' THEN
        IF v_type = 'Sports'    AND v_mins > 60  THEN
            RAISE EXCEPTION 'Faculty may book a sports venue for at most 1 hour';
        ELSIF v_type IN ('Classroom', 'Other') AND v_mins > 180 THEN
            RAISE EXCEPTION 'Faculty may book a classroom for at most 3 hours';
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_booking_duration
BEFORE INSERT ON Booking
FOR EACH ROW EXECUTE FUNCTION fn_booking_duration();

-- ===============================================================
-- 2. BEFORE INSERT: facility availability
--    Maintenance blocks booking; classroom window rule via
--    check_classroom_availability(); sports venues open 06:00-22:00;
--    other venues open 08:00-22:00.
-- ===============================================================
CREATE OR REPLACE FUNCTION fn_booking_availability() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
DECLARE
    v_type facility_type;
BEGIN
    SELECT FacilityType INTO v_type FROM Facility WHERE FacilityID = NEW.FacilityID;

    IF has_maintenance_conflict(NEW.FacilityID, NEW.BookingDate, NEW.StartTime, NEW.EndTime) THEN
        RAISE EXCEPTION 'Facility is under maintenance for the requested slot';
    END IF;

    IF v_type = 'Classroom'
       AND NOT check_classroom_availability(NEW.FacilityID, NEW.BookingDate, NEW.StartTime, NEW.EndTime) THEN
        RAISE EXCEPTION 'Classroom is not available for booking at the requested time';
    END IF;

    IF v_type = 'Sports' AND (NEW.StartTime < TIME '06:00' OR NEW.EndTime > TIME '22:00') THEN
        RAISE EXCEPTION 'Sports venues can only be booked between 06:00 and 22:00';
    END IF;

    IF v_type = 'Other' AND (NEW.StartTime < TIME '08:00' OR NEW.EndTime > TIME '22:00') THEN
        RAISE EXCEPTION 'Other venues can only be booked between 08:00 and 22:00';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_booking_classroom_availability
BEFORE INSERT ON Booking
FOR EACH ROW EXECUTE FUNCTION fn_booking_availability();

-- ===============================================================
-- 3. BEFORE INSERT: advance-booking window and no past slots
--    Students up to 7 days ahead, faculty up to 14 (admin unrestricted).
-- ===============================================================
CREATE OR REPLACE FUNCTION fn_booking_advance_window() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
DECLARE
    v_role user_role;
    v_max  INT;
BEGIN
    SELECT Role INTO v_role FROM Users WHERE UserID = NEW.UserID;

    IF (NEW.BookingDate + NEW.StartTime) <= CURRENT_TIMESTAMP THEN
        RAISE EXCEPTION 'Cannot book a slot that has already started';
    END IF;

    v_max := CASE v_role WHEN 'Student' THEN 7 WHEN 'Faculty' THEN 14 ELSE NULL END;
    IF v_max IS NOT NULL AND NEW.BookingDate > CURRENT_DATE + v_max THEN
        RAISE EXCEPTION '% can book at most % days in advance', v_role, v_max;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_booking_advance_window
BEFORE INSERT ON Booking
FOR EACH ROW EXECUTE FUNCTION fn_booking_advance_window();

-- ===============================================================
-- 4. AFTER UPDATE: auto-reject on confirmation (WF2)
--    When a booking becomes Confirmed:
--      a) abort if the user already has an overlapping Confirmed booking
--      b) abort if the facility already has an overlapping Confirmed booking
--      c) reject every other overlapping Pending booking for the same
--         facility and date (each rejection is logged by trg_booking_audit_log)
--    Raising in (a)/(b) rolls back the whole confirming UPDATE.
--    NOTE: report text matches the exact same (Facility, Date, Start, End);
--    this uses time *overlap* so partially overlapping requests cannot slip through.
-- ===============================================================
CREATE OR REPLACE FUNCTION fn_booking_auto_reject() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM Booking o
               WHERE o.BookingID <> NEW.BookingID
                 AND o.UserID = NEW.UserID
                 AND o.Status = 'Confirmed'
                 AND o.BookingDate = NEW.BookingDate
                 AND o.StartTime < NEW.EndTime AND o.EndTime > NEW.StartTime) THEN
        RAISE EXCEPTION 'User % already has a confirmed booking overlapping this slot', NEW.UserID;
    END IF;

    IF EXISTS (SELECT 1 FROM Booking o
               WHERE o.BookingID <> NEW.BookingID
                 AND o.FacilityID = NEW.FacilityID
                 AND o.Status = 'Confirmed'
                 AND o.BookingDate = NEW.BookingDate
                 AND o.StartTime < NEW.EndTime AND o.EndTime > NEW.StartTime) THEN
        RAISE EXCEPTION 'Facility % already has a confirmed booking overlapping this slot', NEW.FacilityID;
    END IF;

    UPDATE Booking
       SET Status = 'Rejected'
     WHERE BookingID <> NEW.BookingID
       AND FacilityID = NEW.FacilityID
       AND BookingDate = NEW.BookingDate
       AND Status = 'Pending'
       AND StartTime < NEW.EndTime AND EndTime > NEW.StartTime;
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_booking_auto_reject
AFTER UPDATE OF Status ON Booking
FOR EACH ROW
WHEN (NEW.Status = 'Confirmed' AND OLD.Status IS DISTINCT FROM 'Confirmed')
EXECUTE FUNCTION fn_booking_auto_reject();

-- ===============================================================
-- 5. AFTER INSERT / UPDATE: audit log
--    Writes a BookingStatusLog row for the initial status and every change.
-- ===============================================================
CREATE OR REPLACE FUNCTION fn_booking_audit_log() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
DECLARE
    v_actor BIGINT := NULLIF(current_setting('app.current_user_id', true), '')::BIGINT;
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO BookingStatusLog (BookingID, OldStatus, NewStatus, ChangedByUserID)
        VALUES (NEW.BookingID, NULL, NEW.Status::text, COALESCE(v_actor, NEW.UserID));
    ELSIF NEW.Status IS DISTINCT FROM OLD.Status THEN
        INSERT INTO BookingStatusLog (BookingID, OldStatus, NewStatus, ChangedByUserID)
        VALUES (NEW.BookingID, OLD.Status::text, NEW.Status::text, v_actor);
    END IF;
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_booking_audit_log
AFTER INSERT OR UPDATE OF Status ON Booking
FOR EACH ROW EXECUTE FUNCTION fn_booking_audit_log();
