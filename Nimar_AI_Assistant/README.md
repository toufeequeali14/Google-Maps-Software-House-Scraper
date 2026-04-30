# Nimar Production url
https://app.nimar.gov.pk

# AI Assistant URL:
https://app.nimar.gov.pk/aiAssistant


# user
madni

# pass
#676F924c

# run below commands
celery -A celery_scheduler worker -l info

celery -A celery_scheduler beat -l info