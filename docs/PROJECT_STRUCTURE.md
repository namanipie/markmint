# Project Structure

This document outlines the architecture and directory structure of MarkMint to ensure long-term maintainability.

## Root Directories
* backend/ - Python FastAPI application, extraction engines, and MintAI predictive models.
* docs/ - High-level architecture, API contracts, and historical milestone reports.
* scripts/ - Independent scripts for crawling, ingesting, auditing, and database utilities.
* src/ - Next.js frontend application (App Router).
* tests/ - Global and integration test suites.
* data/ - Reserved for local development catalogs.

## Scripts
* scripts/audits/ - Integrity audits and data validation.
* scripts/crawler/ - Resource scraping and downloading tools.
* scripts/curriculum/ - Scripts to manipulate the curriculum catalog.
* scripts/ingestion/ - ETL scripts to load extracted corpus data into the database.
* scripts/migration/ - Data migration tools.
* scripts/utilities/ - Assorted helper scripts.

## Backend Organization
* backend/api/ - FastAPI endpoints and routing logic.
* backend/core/ - Global config, database connections, and versioning.
* backend/models/ - SQLAlchemy database models.
* backend/schemas.py - Pydantic validation schemas.
* backend/services/ - Domain logic isolated by feature (dna, evidence, extraction, families, prediction, scraper).

## Frontend Organization
* src/app/ - Next.js routes and layouts.
* src/components/ - React components.
* src/lib/ - Frontend utilities, API clients, and types.
