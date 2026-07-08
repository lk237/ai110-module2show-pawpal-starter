from pawpal_system import Owner, Pet, Task, Scheduler, Priority

import streamlit as st

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

st.subheader("Quick Demo Inputs")

# The Owner object lives in session_state so it (and its pets/tasks) survives
# Streamlit's top-to-bottom rerun on every widget interaction.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(owner_id=1, name="Jordan")
    st.session_state.next_pet_id = 1
    st.session_state.next_task_id = 1

owner = st.session_state.owner

owner.name = st.text_input("Owner name", value=owner.name)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add pet"):
    # A submitted "add pet" form is handled by Owner.add_pet(), which appends
    # the new Pet to owner.pets. Because owner is stored in session_state, the
    # pet persists across the rerun that Streamlit triggers on button click.
    owner.add_pet(Pet(pet_id=st.session_state.next_pet_id, name=pet_name, species=species))
    st.session_state.next_pet_id += 1

if owner.pets:
    st.write("Current pets:")
    st.table([{"name": p.name, "species": p.species, "tasks": len(p.tasks)} for p in owner.pets])
else:
    st.info("No pets yet. Add one above before adding tasks.")

st.markdown("### Tasks")
st.caption("Add tasks to a pet. These feed into the scheduler below.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

# Choose which pet the task belongs to (Pet.add_task keeps its own list).
pet_choice = None
if owner.pets:
    pet_choice = st.selectbox(
        "Assign to pet",
        options=owner.pets,
        format_func=lambda p: p.name,
    )

if st.button("Add task", disabled=pet_choice is None):
    # Pet.add_task() handles the submitted task data: it wires the task's
    # pet_id back-reference and appends it to that pet's task list.
    pet_choice.add_task(
        Task(
            task_id=st.session_state.next_task_id,
            title=task_title,
            duration_minutes=int(duration),
            priority=Priority[priority.upper()],
        )
    )
    st.session_state.next_task_id += 1

all_tasks = owner.all_tasks()
if all_tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "title": t.title,
                "duration_minutes": t.duration_minutes,
                "priority": t.priority.name.lower(),
            }
            for t in all_tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Builds a daily plan from the owner's pending tasks and time budget.")

if st.button("Generate schedule"):
    scheduler = Scheduler.from_owner(owner)
    plan = scheduler.build_plan(owner)
    st.code(scheduler.explain(plan))
