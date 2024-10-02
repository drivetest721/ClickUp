CREATE DATABASE IF NOT EXISTS DBClickUp;

USE DBClickUp;

CREATE TABLE IF NOT EXISTS ClickUpList (
    ListName VARCHAR(255),
    ListID VARCHAR(255),
    FolderName VARCHAR(255),
    SpaceID VARCHAR(255),
    TaskID VARCHAR(255) PRIMARY KEY,
    TaskSubject VARCHAR(255),
    TaskStartDate BIGINT,
    TaskDueDate BIGINT,
    ParentTaskID VARCHAR(255),
    EstimatedTime BIGINT,
    TaskPriority VARCHAR(50),
    TaskStatus VARCHAR(100),
    AssignByPersonDetails VARCHAR(255),
    TaskAssigneesList TEXT,
    WatchersList TEXT,
    TaskCreatedDate BIGINT,
    TaskUpdateDate BIGINT,
    TaskDateClosed BIGINT,
    TaskDateDone BIGINT,
    TaskTags TEXT,
    TaskDependencies JSON,
    TaskIsMilestone BOOLEAN DEFAULT FALSE,
    TaskIntensity INT DEFAULT 1
);




AccuVelocity: https://app.clickup.com/9002161791/v/li/901601699012
Lecroy - GUIFQT: https://app.clickup.com/9002161791/v/li/900201614016
IKIO - COGSAnalyzer: https://app.clickup.com/9002161791/v/li/901604035672
Airen group - Registry Automation: https://app.clickup.com/9002161791/v/li/901604046396
Airen group - Customer List: https://app.clickup.com/9002161791/v/li/901604046411
Parag Traders - AccuVelocity: https://app.clickup.com/9002161791/v/li/901604272654
ERPNext - https://app.clickup.com/9002161791/v/li/901600183071
ClickUp - https://app.clickup.com/9002161791/v/li/901603806927
Drake = https://app.clickup.com/9002161791/v/li/901603898346