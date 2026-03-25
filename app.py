from datetime import date

import streamlit as st

from pawpal_system import CareTask, Owner, Pet, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

if "owner" not in st.session_state:
    st.session_state.owner = None
if "current_pet" not in st.session_state:
    st.session_state.current_pet = None

st.subheader("Owner & pet")
st.caption("Register once, then add tasks below. Data is kept in `st.session_state` across reruns.")

owner_name = st.text_input("Owner name", value="Jordan")
owner_minutes = st.number_input(
    "Available minutes per day", min_value=15, max_value=1440, value=120, step=15
)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
pet_age = st.number_input("Pet age (years)", min_value=0, max_value=40, value=3)

if st.button("Register owner & pet"):
    owner = Owner(name=owner_name, available_minutes_per_day=int(owner_minutes))
    pet = Pet(name=pet_name, species=species, age=int(pet_age))
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.current_pet = pet
    st.success(f"Registered {owner.name} and {pet.name}.")

if st.session_state.owner and st.session_state.current_pet:
    o = st.session_state.owner
    p = st.session_state.current_pet
    st.info(
        f"Active profile: **{o.name}** ({o.get_daily_capacity()} min/day) · "
        f"**{p.name}** ({p.species}, age {p.age})"
    )

st.markdown("### Tasks")
st.caption("Tasks are stored on your pet via `Pet.add_task` and used by the scheduler.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    task_type = st.selectbox(
        "Task type",
        ["exercise", "feeding", "grooming", "general"],
        index=0,
    )

if st.button("Add task"):
    if st.session_state.owner is None or st.session_state.current_pet is None:
        st.error("Register an owner and pet first.")
    else:
        task = CareTask(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            task_type=task_type,
        )
        st.session_state.current_pet.add_task(task)
        st.success(f"Added “{task.title}” for {st.session_state.current_pet.name}.")

tasks_for_display = []
if st.session_state.owner and st.session_state.current_pet:
    for t in st.session_state.current_pet.get_tasks():
        tasks_for_display.append(
            {
                "title": t.title,
                "duration_minutes": t.duration_minutes,
                "priority": t.priority,
                "task_type": t.task_type,
                "description": t.describe(),
            }
        )

if tasks_for_display:
    st.write("Current tasks:")
    st.table(tasks_for_display)
else:
    st.info("No tasks yet. Register a pet and add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Uses `Scheduler.generate_plan` with your owner, pet, and tasks.")

if st.button("Generate schedule"):
    if st.session_state.owner is None or st.session_state.current_pet is None:
        st.error("Register an owner and pet first.")
    elif not st.session_state.current_pet.get_tasks():
        st.warning("Add at least one task before generating a schedule.")
    else:
        owner = st.session_state.owner
        pet = st.session_state.current_pet
        scheduler = Scheduler(owner=owner, pet=pet, tasks=pet.get_tasks())
        plan = scheduler.generate_plan(date.today())
        st.success(f"Plan for **{plan.date.isoformat()}**")
        if plan.scheduled_items:
            st.table(plan.to_display_rows())
        else:
            st.info("No tasks fit in the schedule with the current settings.")
        if plan.unscheduled_tasks:
            st.subheader("Unscheduled")
            st.write([t.title for t in plan.unscheduled_tasks])
        st.text(plan.explain())
