# app/__init__.py
# This file is now simplified for the Firebase deployment model.

from flask import Blueprint, session, flash, redirect, url_for, render_template

# The database logic will be moved to a separate module for Firestore,
# but for now, we'll keep the file minimal to avoid errors.

# Note: The database connection logic will be re-written to use Firestore.
# SQLite is not compatible with a serverless environment like Firebase.
