-- UNIreserve: Campus Facility Booking System (BITS Pilani Hyderabad)
-- schema.sql: types, tables, constraints, indexes, views
-- Run order: schema.sql -> procedures.sql -> triggers.sql -> seed.sql

-- ---------------------------------------------------------------
-- Drop guards (development only: lets this file be re-run cleanly).
-- WARNING: destroys all data. After re-running, also re-run procedures.sql,
-- triggers.sql and seed.sql (dropping the tables removes their triggers).
-- ---------------------------------------------------------------
DROP VIEW  IF EXISTS booking_summary_view, facility_availability_view;
DROP TABLE IF EXISTS BookingStatusLog, Booking, MaintenanceSchedule, Holiday,
                     Classroom, SportsVenue, Facility,
                     Admin, Faculty, Student, Users CASCADE;
DROP TYPE  IF EXISTS booking_status, indoor_outdoor, facility_status, facility_type, user_role CASCADE;

-- ---------------------------------------------------------------
-- Enumerated types
-- ---------------------------------------------------------------
CREATE TYPE user_role       AS ENUM ('Student', 'Faculty', 'Admin');
CREATE TYPE facility_type   AS ENUM ('Sports', 'Classroom');
CREATE TYPE facility_status AS ENUM ('Active', 'Under Maintenance');
CREATE TYPE indoor_outdoor  AS ENUM ('Indoor', 'Outdoor');
CREATE TYPE booking_status  AS ENUM ('Pending', 'Confirmed', 'Rejected', 'Cancelled', 'Completed');

-- ---------------------------------------------------------------
-- User hierarchy (IS-A, horizontal split, shared PK)
-- "User" is a reserved word in PostgreSQL, so the superclass table is Users.
-- ---------------------------------------------------------------
CREATE TABLE Users (
    UserID       SERIAL PRIMARY KEY,
    Name         VARCHAR(100) NOT NULL,
    Email        VARCHAR(150) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    Phone        VARCHAR(20),
    Role         user_role    NOT NULL,
    CreatedAt    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Student (
    UserID     INT PRIMARY KEY REFERENCES Users(UserID) ON DELETE CASCADE,
    BITS_ID    VARCHAR(13) NOT NULL UNIQUE,
    Department VARCHAR(100),
    Year       INT NOT NULL CHECK (Year BETWEEN 1 AND 5)
);

CREATE TABLE Faculty (
    UserID      INT PRIMARY KEY REFERENCES Users(UserID) ON DELETE CASCADE,
    EmployeeID  VARCHAR(20) NOT NULL UNIQUE,
    Department  VARCHAR(100),
    Designation VARCHAR(100)
);

CREATE TABLE Admin (
    UserID     INT PRIMARY KEY REFERENCES Users(UserID) ON DELETE CASCADE,
    AdminLevel VARCHAR(50)
);

-- ---------------------------------------------------------------
-- Facility hierarchy (IS-A, horizontal split, shared PK)
-- ---------------------------------------------------------------
CREATE TABLE Facility (
    FacilityID   SERIAL PRIMARY KEY,
    Name         VARCHAR(100) NOT NULL,
    Location     VARCHAR(150),
    FacilityType facility_type   NOT NULL,
    Status       facility_status NOT NULL DEFAULT 'Active'
);

CREATE TABLE SportsVenue (
    FacilityID    INT PRIMARY KEY REFERENCES Facility(FacilityID) ON DELETE CASCADE,
    VenueType     VARCHAR(50),
    Surface       VARCHAR(50),
    IndoorOutdoor indoor_outdoor NOT NULL
);

CREATE TABLE Classroom (
    FacilityID   INT PRIMARY KEY REFERENCES Facility(FacilityID) ON DELETE CASCADE,
    BuildingName VARCHAR(100) NOT NULL,
    RoomNumber   VARCHAR(20)  NOT NULL,
    Capacity     INT NOT NULL CHECK (Capacity > 0),
    HasProjector BOOLEAN NOT NULL DEFAULT FALSE,
    HasAC        BOOLEAN NOT NULL DEFAULT FALSE,
    RoomType     VARCHAR(50)
);

-- ---------------------------------------------------------------
-- Booking (core transactional table)
-- Slots are 30-minute increments (assumption in report section 6).
-- ---------------------------------------------------------------
CREATE TABLE Booking (
    BookingID  SERIAL PRIMARY KEY,
    UserID     INT NOT NULL REFERENCES Users(UserID)       ON DELETE RESTRICT,
    FacilityID INT NOT NULL REFERENCES Facility(FacilityID) ON DELETE RESTRICT,
    BookingDate DATE NOT NULL,
    StartTime   TIME NOT NULL,
    EndTime     TIME NOT NULL,
    Status      booking_status NOT NULL DEFAULT 'Pending',
    Purpose     VARCHAR(255),
    CreatedAt   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_booking_time_order CHECK (EndTime > StartTime),
    CONSTRAINT chk_booking_slot_grid  CHECK (
        EXTRACT(MINUTE FROM StartTime) IN (0, 30) AND EXTRACT(SECOND FROM StartTime) = 0 AND
        EXTRACT(MINUTE FROM EndTime)   IN (0, 30) AND EXTRACT(SECOND FROM EndTime)   = 0
    )
);

CREATE TABLE MaintenanceSchedule (
    ScheduleID  SERIAL PRIMARY KEY,
    FacilityID  INT NOT NULL REFERENCES Facility(FacilityID) ON DELETE CASCADE,
    StartDate   DATE NOT NULL,
    EndDate     DATE NOT NULL,
    StartTime   TIME NOT NULL,
    EndTime     TIME NOT NULL,
    Description VARCHAR(255),
    CONSTRAINT chk_maint_dates CHECK (EndDate >= StartDate)
);

CREATE TABLE Holiday (
    HolidayID   SERIAL PRIMARY KEY,
    HolidayDate DATE NOT NULL UNIQUE,
    Description VARCHAR(255)
);

-- Audit trail; populated by trigger trg_booking_audit_log
CREATE TABLE BookingStatusLog (
    LogID           SERIAL PRIMARY KEY,
    BookingID       INT NOT NULL REFERENCES Booking(BookingID) ON DELETE CASCADE,
    OldStatus       VARCHAR(20),
    NewStatus       VARCHAR(20) NOT NULL,
    ChangedByUserID INT REFERENCES Users(UserID) ON DELETE SET NULL,
    ChangedAt       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------
-- Indexes
-- (Users.Email already has a unique index from its UNIQUE constraint.)
-- ---------------------------------------------------------------
-- Composite index for availability / range lookups (WF1, WF3)
CREATE INDEX idx_booking_facility_date_start ON Booking (FacilityID, BookingDate, StartTime);
-- Filter by status (admin queues, analytics)
CREATE INDEX idx_booking_status ON Booking (Status);
-- "My bookings" lookups (WF4)
CREATE INDEX idx_booking_user_date ON Booking (UserID, BookingDate);
-- Admin pending queue (WF2)
CREATE INDEX idx_booking_pending ON Booking (FacilityID, BookingDate) WHERE Status = 'Pending';
CREATE INDEX idx_maint_facility_dates ON MaintenanceSchedule (FacilityID, StartDate, EndDate);
CREATE INDEX idx_statuslog_booking ON BookingStatusLog (BookingID, ChangedAt);

-- ---------------------------------------------------------------
-- Views (WF3)
-- ---------------------------------------------------------------
-- Upcoming occupied slots per facility (confirmed = blocked, pending = load)
CREATE VIEW facility_availability_view AS
SELECT f.FacilityID,
       f.Name         AS FacilityName,
       f.FacilityType,
       f.Status       AS FacilityStatus,
       b.BookingDate,
       b.StartTime,
       b.EndTime,
       b.Status       AS BookingStatus
FROM Facility f
LEFT JOIN Booking b
       ON b.FacilityID = f.FacilityID
      AND b.BookingDate >= CURRENT_DATE
      AND b.Status IN ('Pending', 'Confirmed');

-- Per-facility weekly stats
CREATE VIEW booking_summary_view AS
SELECT f.FacilityID,
       f.Name AS FacilityName,
       DATE_TRUNC('week', b.BookingDate)::date AS WeekStart,
       COUNT(*)                                          AS TotalRequests,
       COUNT(*) FILTER (WHERE b.Status = 'Confirmed')    AS Confirmed,
       COUNT(*) FILTER (WHERE b.Status = 'Pending')      AS Pending,
       COUNT(*) FILTER (WHERE b.Status = 'Rejected')     AS Rejected,
       COUNT(*) FILTER (WHERE b.Status = 'Cancelled')    AS Cancelled,
       COALESCE(SUM(EXTRACT(EPOCH FROM (b.EndTime - b.StartTime)) / 3600)
                FILTER (WHERE b.Status IN ('Confirmed', 'Completed')), 0) AS BookedHours
FROM Booking b
JOIN Facility f ON f.FacilityID = b.FacilityID
GROUP BY f.FacilityID, f.Name, DATE_TRUNC('week', b.BookingDate);
