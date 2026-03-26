# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
--> I included these classes:
## PawPal+ Class Design

## PawPal+ Class Design

1) Owner:
    Attributes:
        name
        available_time_per_day
        preferred_schedule (morning/evening/flexible)
        experience_level (new, intermediate, expert)
        preferences (likes/dislikes for tasks)

    Methods:
        set_preferences(preferences)
        update_availability(time)
        get_available_time()
        adjust_task_priority(task)


2) Pet:
    Attributes:
        name
        species
        age
        energy_level
        special_needs

    Methods:
        get_daily_needs()
        adjust_task_priority(task)


3) Task:
    Attributes:
        name
        duration
        priority
        category
        is_mandatory
        deadline

    Methods:
        get_priority_score()
        is_urgent(current_time)


4) Constraint:
    Attributes:
        max_time_available
        preferred_times
        task_limits

    Methods:
        is_task_allowed(task)
        can_fit(task, remaining_time)


5) Schedule:
    Attributes:
        tasks
        total_time
        unused_time

    Methods:
        add_task(task)
        get_summary()
        validate(constraints)


6) Planner:
    Attributes:
        pet
        owner
        tasks
        constraints

    Methods:
        generate_plan()
        prioritize_tasks()
        optimize_schedule()
        explain_plan()


7) UserPreferences:
    Attributes:
        preferred_task_times
        disliked_tasks
        routine_style

    Methods:
        adjust_priority(task)
        filter_tasks(tasks)


8) ExplanationEngine:
    Attributes:
        None

    Methods:
        explain(schedule)
        justify_task(task)
**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
--> Yes. The UML code given by claude had some mistakes. It did not account for a lot of relationships (For ex. 'Owner has pets'). Mistakes rectified later .
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
