FROM ubuntu:16.04
RUN apt-get update &&\
    apt-get install -y wget
RUN wget -q -O - https://jenkins-ci.org/debian/jenkins-ci.org.key | apt-key add - &&\
    sh -c 'echo deb http://pkg.jenkins-ci.org/debian binary/ > /etc/apt/sources.list.d/jenkins.list' &&\
    apt-get update &&\
    apt-get install -y default-jre &&\
    apt-get install -y default-jdk &&\
    apt-get install -y jenkins
EXPOSE 8080
#ADD run.sh /tmp/
#RUN chmod 777 /tmp/*.sh
#CMD /tmp/run.sh
