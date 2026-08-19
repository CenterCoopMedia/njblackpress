# Issue specifications

## Issue 25 — Read the 26 newspaper pages and log what's in them

**State:** OPEN

Go through the 26 newspaper page captures. For each one, log people named, dates, incidents, and any connections to other records. Done when every page has a log entry.

## Issue 26 — Read the 10 Herald News and Newark Herald issues

**State:** OPEN

Go through the 10 Herald News and Newark Herald issues we captured. Log people, dates, incidents, and connections the same way as the other reads. Done when all 10 have a log entry.

## Issue 27 — Pull the throughlines into an editorial memo

**State:** OPEN

Once the reads are done, look across all of them for repeat names, places, and events. Write a short memo naming the strongest narrative threads worth telling. Done when the memo is written and shared.

## Issue 28 — Build events.json and stories.json from the readings

**State:** OPEN

Turn the logged people, dates, and incidents into two data files: events.json (dated incidents) and stories.json (narrative threads). Done when both files exist and validate against the site's data conventions.

## Issue 29 — Sort the Internet Archive files as public domain

**State:** OPEN

Confirm every Internet Archive capture is public domain and mark it publishable as-is in the manifest. Done when all Internet Archive files have a publish status.

## Issue 30 — Mark newspapers.com files as crop-first, cited clips only

**State:** OPEN

Newspapers.com material can't publish as full pages. Go through each file, decide what clip and citation is needed, and mark it crop-first in the manifest. Done when every newspapers.com file has a crop plan.

## Issue 31 — Mark Danky book scans as citation-text only

**State:** OPEN

Danky book scans can't publish as images. Mark each one citation-text only in the manifest, with the text we'll quote. Done when every Danky scan has a citation entry.

## Issue 32 — Build the publishable/not/crop-first manifest

**State:** OPEN

Combine the rights calls for Internet Archive, newspapers.com, Danky, and wayback screenshots into one manifest file covering every record. Done when the manifest lists a status for every file in the catalog.

## Issue 33 — Add an evidence array to each publication

**State:** OPEN

Extend publications.json with an evidence array per publication, linking to the source-catalog files and the rights manifest. Done when every publication with source material has its evidence listed.

## Issue 34 — Add events.json and stories.json to the site data

**State:** OPEN

Wire the events and stories files from milestone 2 into the site's data folder and metadata block, matching the existing publications.json conventions. Done when the frontend can load both files.

## Issue 35 — Update convert_csv.py and the data pipeline for the new fields

**State:** OPEN

The CSV-to-JSON pipeline doesn't know about evidence, events, or stories yet. Update convert_csv.py so a future Notion export still produces valid data. Done when a fresh conversion round-trips without losing the new fields.

## Issue 36 — Write a data dictionary for the new schema

**State:** OPEN

Document the new evidence, events, and stories fields the same way CLAUDE.md documents the existing data model, so the redesign work can build against a stable spec. Done when the schema is written down.

## Discussion 47 — Last 3 comments

### Comment 1
**Date:** August 19, 2026 at 4:31 PM

Big milestone: every publication in the archive now has clean, high-quality archival records.

Over the past two days we replaced all the blurry, partial screenshots from our first research pass with proper full-resolution files. That means 26 newspaper pages from the 1880s through the 2020s saved at print quality, 18 clean snapshots of publication websites, 10 complete issues of Newark's Black newspapers from 1938–1942 (which are public domain, so we can publish them), and 6 newly discovered items — including a first issue of MEDIC News from the Newark Public Library's collections and a full 2022 issue of The Nubian News.

We also confirmed something important: for about 93 of the smaller publications (newsletters, camp papers, short-run magazines), no digitized copies exist anywhere. For those, the 1998 scholarly catalog entry we already have is genuinely the best available record — now that's documented rather than an open question.

Next up: actually reading everything we collected to find the stories and themes worth telling, and sorting out exactly which materials we're allowed to publish on the public site. Those are milestones 2 and 3 on this project board.
