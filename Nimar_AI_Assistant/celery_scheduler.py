import asyncio
from celery import Celery
from celery.schedules import crontab
from AI_Assistant_Automation import run
from datetime import datetime, timezone

app = Celery(
    "nimar_scheduler",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

app.conf.update(
    broker_url="redis://localhost:6379/0",
    result_backend="redis://localhost:6379/0",
    timezone="Asia/Karachi",


    beat_schedule={

        # Every 5 minutes
        "nimar-every-5-minutes":{
            "task": "celery_scheduler.send_daily_prompt",
            "schedule": crontab(minute="*/5") # every 5 minutes  # for 30 minutes: (0,30)
        },

        # Exact 9: 00 am
        "daily-nimar-prompt-9am": {
            "task": "celery_scheduler.send_daily_prompt",
            "schedule": crontab(hour=9, minute=0)  #
        },
 
 
    },
    #  This prevents firing missed tasks on startup
    beat_max_loop_interval=300,
)





@app.task(name="celery_scheduler.send_daily_prompt")
def send_daily_prompt():
    print(f"Running daily Nimar AI Assistant prompt at {datetime.now()}...")
    asyncio.run(run())
    print("Done.")



















#It will also execute the missed tasks
# import asyncio
# from celery import Celery
# from celery.schedules import crontab
# from AI_Assistant_Automation import run

# app = Celery(
#     "nimar_scheduler",
#     broker="redis://localhost:6379/0",
#     backend="redis://localhost:6379/0",
# )

# app.conf.update(
#     broker_url="redis://localhost:6379/0",
#     result_backend="redis://localhost:6379/0",
#     timezone="Asia/Karachi",
#     beat_schedule={
#         "daily-nimar-prompt-9pm": {
#             "task": "celery_scheduler.send_daily_prompt",
#             "schedule": crontab(hour=5, minute=10),
#         },
#     },
# )


# @app.task(name="celery_scheduler.send_daily_prompt")
# def send_daily_prompt():
#     print("Running daily Nimar AI Assistant prompt...")
#     asyncio.run(run())
#     print("Done.")

    #celery -A celery worker --beat --loglevel=info