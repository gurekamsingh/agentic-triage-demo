#!/usr/bin/env python3
"""
Task Manager API — FastAPI
Intentional bugs planted for agentic triage demo.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import os

app = FastAPI(title="Task Manager")

DATA_FILE = "tasks.json"

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_tasks() -> list:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        # BUG 3 (big): No error handling if file is corrupted JSON
        return json.load(f)


def save_tasks(tasks: list):
    with open(DATA_FILE, "w") as f:
        json.dump(tasks, f)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    title: str
    description: str = ""


class TaskUpdate(BaseModel):
    completed: bool


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def index():
    with open("templates/index.html") as f:
        return f.read()


@app.get("/tasks")
def list_tasks():
    return load_tasks()


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    # BUG 1 (small): No validation — empty title is accepted
    tasks = load_tasks()

    # BUG 2 (small): ID logic breaks after deletion
    # Uses len(tasks) instead of max(id) + 1
    new_id = len(tasks) + 1

    new_task = {
        "id": new_id,
        "title": task.title,
        "description": task.description,
        "completed": False,
    }
    tasks.append(new_task)
    save_tasks(tasks)
    return new_task


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            return task
    # BUG 4 (small): Should return 404, returns 200 with error message
    return {"error": "Task not found"}


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, update: TaskUpdate):
    tasks = load_tasks()

    # BUG 5 (big): Race condition — load, modify, save is not atomic
    # Two simultaneous requests can overwrite each other
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = update.completed
            save_tasks(tasks)
            return task

    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    # BUG 6 (big): No authentication — anyone can delete any task
    tasks = load_tasks()
    updated = [t for t in tasks if t["id"] != task_id]

    if len(updated) == len(tasks):
        raise HTTPException(status_code=404, detail="Task not found")

    save_tasks(updated)
    return {"message": f"Task {task_id} deleted"}