FROM jenkins/jenkins:lts-jdk21
USER root
RUN sed -i "s|http://|https://|g" /etc/apt/sources.list.d/debian.sources && apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip git && rm -rf /var/lib/apt/lists/*
USER jenkins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false" CASC_JENKINS_CONFIG=/var/jenkins_home/casc.yaml
COPY casc.yaml /var/jenkins_home/casc.yaml
