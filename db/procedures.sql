-- procedures.sql: stored functions / procedures
-- Must run after schema.sql and before triggers.sql (triggers call these).

-- ---------------------------------------------------------------
-- Maintenance conflict: TRUE if the facility is Under Maintenance or has a
-- MaintenanceSchedule window overlapping the requested slot.
-- ---------------------------------------------------------------
CREATE OR REPLACE FUNCTION has_maintenance_conflict(
    p_facility_id INT, p_date DATE, p_start TIME, p_end TIME
) RETURNS BOOLEAN
LANGUAGE sql STABLE AS $$
    SELECT EXISTS (SELECT 1 FROM Facility
                   WHERE FacilityID = p_facility_id AND Status = 'Under Maintenance')
        OR EXISTS (SELECT 1 FROM MaintenanceSchedule m
                   WHERE m.FacilityID = p_facility_id
                     AND p_date BETWEEN m.StartDate AND m.EndDate
                     AND p_start < m.EndTime
                     AND p_end   > m.StartTime);
$$;

-- ---------------------------------------------------------------
-- check_classroom_availability (report sections 4 and 7)
-- Classrooms: weekdays only from 18:00 (until 22:00);
--             weekends and declared holidays 08:00-22:00.
-- Non-classroom facilities are not restricted by this function (returns TRUE);
-- sports-venue hours (06:00-22:00) are enforced in the availability trigger.
-- ---------------------------------------------------------------
CREATE OR REPLACE FUNCTION check_classroom_availability(
    p_facility_id INT, p_date DATE, p_start TIME, p_end TIME
) RETURNS BOOLEAN
LANGUAGE plpgsql STABLE AS $$
DECLARE
    v_type    facility_type;
    v_offday  BOOLEAN;
BEGIN
    SELECT FacilityType INTO v_type FROM Facility WHERE FacilityID = p_facility_id;
    IF v_type IS NULL OR v_type <> 'Classroom' THEN
        RETURN TRUE;
    END IF;

    v_offday := EXTRACT(DOW FROM p_date) IN (0, 6)
                OR EXISTS (SELECT 1 FROM Holiday WHERE HolidayDate = p_date);

    IF v_offday THEN
        RETURN p_start >= TIME '08:00' AND p_end <= TIME '22:00';
    END IF;
    RETURN p_start >= TIME '18:00' AND p_end <= TIME '22:00';
END;
$$;

-- ---------------------------------------------------------------
-- cancel_booking (WF4): verifies ownership + 2-hour window, sets Cancelled.
-- Runs inside the caller's transaction. The status-change audit row is written
-- by trg_booking_audit_log, which picks up the acting user from app.current_user_id.
-- ---------------------------------------------------------------
CREATE OR REPLACE FUNCTION cancel_booking(p_booking_id INT, p_user_id INT)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    b Booking%ROWTYPE;
BEGIN
    SELECT * INTO b FROM Booking WHERE BookingID = p_booking_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Booking % does not exist', p_booking_id;
    END IF;
    IF b.UserID <> p_user_id THEN
        RAISE EXCEPTION 'Booking % does not belong to user %', p_booking_id, p_user_id;
    END IF;
    IF b.Status NOT IN ('Pending', 'Confirmed') THEN
        RAISE EXCEPTION 'Booking % is % and cannot be cancelled', p_booking_id, b.Status;
    END IF;
    IF (b.BookingDate + b.StartTime) - CURRENT_TIMESTAMP < INTERVAL '2 hours' THEN
        RAISE EXCEPTION 'Cancellations must be made at least 2 hours before the start time';
    END IF;

    PERFORM set_config('app.current_user_id', p_user_id::text, true);
    UPDATE Booking SET Status = 'Cancelled' WHERE BookingID = p_booking_id;
END;
$$;
