# Use the official Python image, specifying version 3.11.4
FROM python:3.11.4-slim-buster

# Set the working directory in the container
WORKDIR /app/save-report-data-to-mongo

COPY . /app/save-report-data-to-mongo
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask app's port
#local pgbadger report port
EXPOSE 8011 
# flask UI port
EXPOSE 8012 

RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

# CMD ["python", "scripts/app.py"]
# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/supervisord.conf

# Command to start Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
#BUILD IMG
#docker build -t load-report-generator .

# remove "desktop" here: it worked
# (raghava_venv) cat ~/.docker/config.json
# {
#         "auths": {},
#         "credsStore": "desktop",
#         "currentContext": "desktop-linux",
#         "plugins": {
#                 "debug": {
#                         "hooks": "exec"
#                 },
#                 "scout": {
#                         "hooks": "pull,buildx build"
#                 }
#         },
#         "features": {
#                 "hooks": "true"
#         }
# }%     