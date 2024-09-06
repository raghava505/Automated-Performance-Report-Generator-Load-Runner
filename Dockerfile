# Use the official Python image, specifying version 3.11.4
FROM python:3.11.4-slim-buster

# Set the working directory in the container
WORKDIR /app/save-report-data-to-mongo

COPY . /app/save-report-data-to-mongo
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask app's port
EXPOSE 5000

CMD ["python", "scripts/app.py"]

#BUILD IMG
#docker build -t report-generator .

#RUN container
# docker run -d -p 5000:5000 --name report-generator report-generator

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