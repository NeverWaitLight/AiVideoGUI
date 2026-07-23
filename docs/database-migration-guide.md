# Database Migration Guide - UUID to BigInteger IDs

## Overview

This guide explains how to migrate your existing AI Video GUI database from UUID String primary keys and DateTime timestamps to BigInteger autoincrement IDs and millisecond integer timestamps.

## Migration File

**Location:** `alembic/versions/20260723_migrate_to_bigint_ids_and_timestamps.py`

**Revision ID:** `20260723_bigint`

**Revises:** `b2bd28c1ce35` (Initial SQLAlchemy ORM schema)

## What This Migration Does

### ID Conversion
- Converts all UUID String primary keys (36-character strings) to BigInteger autoincrement IDs
- Maintains data order based on `created_at` timestamp
- Updates all foreign key relationships to use new Integer IDs

### Timestamp Conversion
- Converts all DateTime columns to millisecond integer timestamps
- Format: `CAST(strftime('%s', datetime_field) * 1000 AS INTEGER)`
- Handles missing `updated_at` fields by using `created_at` as fallback

### Tables Migrated (14 tables total)

**Phase 1: Root table**
1. `projects` - UUID → BigInteger

**Phase 2: Tables depending on projects**
2. `conversations` - UUID → BigInteger
3. `scripts` - UUID → BigInteger
4. `outlines` - UUID → BigInteger
5. `shot_history` - UUID → BigInteger
6. `characters` - Integer ID preserved, but `project_id` foreign key updated

**Phase 3: Tables depending on Phase 2**
7. `messages` - UUID → BigInteger
8. `scenes` - UUID → BigInteger
9. `outline_history` - UUID → BigInteger
10. `script_history` - UUID → BigInteger

**Phase 4: Tables depending on Phase 3**
11. `shots` - UUID → BigInteger
12. `active_tasks` - String primary key preserved (task_id), but `message_id` foreign key updated
13. `character_history` - UUID → BigInteger

**Phase 5: Independent tables**
14. `media_files` - UUID → BigInteger

## Prerequisites

### 1. Backup Your Database

**CRITICAL: Create a backup before running the migration!**

### 2. Close the Application

Ensure the AI Video GUI application is completely closed before running the migration.

### 3. Check Current Schema

```bash
cd /c/Users/admin/workspace/ai-video-gui
uv run alembic current
```

Expected output: `b2bd28c1ce35 (head)`

## Running the Migration

### Step 1: Run the Migration

```bash
uv run alembic upgrade head
```

### Step 2: Verify the Migration

```bash
uv run alembic current
```

Expected output: `20260723_bigint (head)`

### Step 3: Test the Application

```bash
uv run main.py
```

## Rollback (Not Supported)

This is a ONE-WAY migration. Downgrade is not supported. If rollback is needed, restore from database backup.

## Migration Strategy

The migration uses a phased approach based on foreign key dependencies:
1. Create mapping tables for UUID to Integer conversion
2. Migrate root tables first (projects)
3. Migrate child tables using mapping tables to convert foreign keys
4. Clean up mapping tables after migration

