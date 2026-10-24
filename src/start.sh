#!/bin/bash
uvicorn app.main:app --host 0.0.0.0 --port 9003 --reload --log-level debug
